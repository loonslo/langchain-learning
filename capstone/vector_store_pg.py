"""可选的 pgvector 后端，强调迁移、幂等与租户边界。"""

from __future__ import annotations

import argparse
import hashlib
import os
from dataclasses import dataclass

from langchain_core.documents import Document

from capstone.config import tenant_key
from capstone.permissions import User, attach_acl
from common import get_embeddings


@dataclass(frozen=True)
class PgVectorSettings:
    connection: str
    collection: str
    dimensions: int
    tenant_id: str

    @classmethod
    def from_env(cls, *, require_connection: bool = True) -> "PgVectorSettings":
        connection = os.getenv("PG_CONN", "").strip()
        if require_connection and not connection:
            raise RuntimeError(
                "缺少 PG_CONN；不要在源码里提供带默认密码的连接串"
            )
        base_collection = os.getenv("PG_COLLECTION", "capstone_kb").strip()
        if not base_collection.replace("_", "").isalnum():
            raise ValueError("PG_COLLECTION 只能包含字母、数字和下划线")
        tenant_id = os.getenv("PG_TENANT_ID", "default").strip().lower()
        dimensions = int(os.getenv("PGVECTOR_DIMENSIONS", "512"))
        if dimensions <= 0:
            raise ValueError("PGVECTOR_DIMENSIONS 必须大于 0")
        return cls(
            connection=connection,
            collection=f"{base_collection}_{tenant_key(tenant_id)}",
            dimensions=dimensions,
            tenant_id=tenant_id,
        )


def deterministic_document_id(document: Document, storage_namespace: str) -> str:
    source = str(document.metadata.get("source", ""))
    page = str(document.metadata.get("page", ""))
    chunk_index = str(document.metadata.get("chunk_index", ""))
    material = (
        f"{storage_namespace}\0{source}\0{page}\0{chunk_index}\0"
        f"{document.page_content}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_pg_filter(user: User, *, topic: str | None = None) -> dict[str, object]:
    """在 SQL 查询前限制租户和 ACL；不能先召回再在 Python 中删结果。"""
    access: list[dict[str, object]] = [
        {"visibility": {"$eq": "public"}},
        {"owner_id": {"$eq": user.user_id}},
    ]
    if user.dept:
        access.append({"dept": {"$eq": user.dept}})
    access.extend(
        {f"acl_role_{role}": {"$eq": True}} for role in sorted(user.roles)
    )
    clauses: list[dict[str, object]] = [
        {"tenant_id": {"$eq": user.tenant_id}},
        {"$or": access},
    ]
    if topic:
        clauses.append({"topic": {"$eq": topic}})
    return {"$and": clauses}


def sample_documents(settings: PgVectorSettings) -> list[Document]:
    rows = (
        ("RAG 通过检索外部文档再生成，减少无依据回答。", "rag"),
        ("pgvector 是 Postgres 的向量扩展，支持 HNSW 等索引。", "infra"),
        ("向量库选型取决于规模、延迟、隔离、备份和团队运维能力。", "infra"),
    )
    documents = []
    for index, (content, topic) in enumerate(rows, 1):
        document = Document(
            page_content=content,
            metadata={
                "source": f"pgvector-sample-{index}",
                "topic": topic,
                "tenant_id": settings.tenant_id,
            },
        )
        documents.append(attach_acl(document, visibility="public"))
    return documents


def build_store(settings: PgVectorSettings):
    """扩展安装和 schema 迁移由 DBA/迁移工具完成，应用账号不自动提权。"""
    try:
        from langchain_postgres import PGVector
    except ImportError as exc:
        raise RuntimeError(
            "缺少可选依赖；安装 requirements-pgvector.txt"
        ) from exc

    store = PGVector(
        embeddings=get_embeddings(),
        collection_name=settings.collection,
        connection=settings.connection,
        use_jsonb=True,
        create_extension=False,
        embedding_length=settings.dimensions,
        collection_metadata={"tenant_id": settings.tenant_id},
    )
    documents = sample_documents(settings)
    ids = [
        deterministic_document_id(document, settings.collection)
        for document in documents
    ]
    store.add_documents(documents, ids=ids)
    return store, len(documents)


def query(store, question: str, user: User, *, topic: str | None = None):
    if not question.strip():
        raise ValueError("question 不能为空")
    return store.similarity_search(
        question,
        k=3,
        filter=build_pg_filter(user, topic=topic),
    )


def hnsw_index_sql(dimensions: int, collection: str = "capstone_kb") -> str:
    """返回迁移模板；先查询集合 UUID，再替换占位符并由 DBA 执行。"""
    if dimensions <= 0:
        raise ValueError("dimensions 必须大于 0")
    suffix = hashlib.sha256(collection.encode("utf-8")).hexdigest()[:12]
    return (
        "-- 以下由迁移/DBA 账号执行，不由应用启动时自动执行：\n"
        "CREATE EXTENSION IF NOT EXISTS vector;\n\n"
        "-- 将 <collection_uuid> 替换为 langchain_pg_collection.uuid；\n"
        "-- CREATE INDEX CONCURRENTLY 不能放在事务块内。\n"
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
        f"langchain_pg_embedding_hnsw_{suffix} ON langchain_pg_embedding\n"
        f"USING hnsw ((embedding::vector({dimensions})) vector_cosine_ops)\n"
        "WHERE collection_id = '<collection_uuid>';"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("diagnose", "migration", "build", "query"),
        nargs="?",
        default="diagnose",
    )
    parser.add_argument("--question", default="生产向量库如何选型？")
    parser.add_argument("--topic")
    parser.add_argument("--user-id", default="public-reader")
    parser.add_argument("--dept", default="")
    parser.add_argument("--role", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = PgVectorSettings.from_env(
        require_connection=args.command in {"build", "query"}
    )
    print(
        f"tenant={settings.tenant_id}, collection={settings.collection}, "
        f"dimensions={settings.dimensions}, PG_CONN={'configured' if settings.connection else 'missing'}"
    )
    if args.command == "diagnose":
        return 0 if settings.connection else 2
    if args.command == "migration":
        print(hnsw_index_sql(settings.dimensions, settings.collection))
        return 0

    store, count = build_store(settings)
    print(f"幂等写入 {count} 条文档（确定性 ID）")
    if args.command == "build":
        return 0
    user = User(
        args.user_id,
        tenant_id=settings.tenant_id,
        dept=args.dept,
        roles=frozenset(args.role),
    )
    for document in query(store, args.question, user, topic=args.topic):
        print(
            f"[{document.metadata.get('source', 'unknown')}] "
            f"{document.page_content}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
