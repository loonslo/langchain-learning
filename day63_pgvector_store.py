"""
Day63 · 生产级向量库：Chroma → pgvector
==========================================================
测试工程师转 AI 应用开发 · 阶段6 上线补全

这天学什么：
- Chroma 适合本地/原型；上生产常换 pgvector（Postgres 的向量扩展）或 Milvus。
- pgvector 的好处：向量和业务数据同库，能用 SQL 做 metadata 过滤、事务、备份，
  运维团队已有的 Postgres 经验直接复用，不用再引一套独立向量库。
- 选型一句话：单机中小规模 → pgvector；亿级 / 高并发专用检索 → Milvus；
  原型 / 嵌入式 → Chroma。

前置（本机要有 Postgres + pgvector 扩展）：
  docker run -d --name pgvec -e POSTGRES_PASSWORD=pass -p 5432:5432 pgvector/pgvector:pg16
  pip install langchain-postgres psycopg[binary]

没有 Postgres 也能读懂：代码结构和 Chroma 几乎一样，区别只在 store 换一个类 + 连接串。
==========================================================
"""

import os
from langchain_core.documents import Document
from common import get_embeddings

CONN = os.getenv("PG_CONN", "postgresql+psycopg://postgres:pass@localhost:5432/postgres")
COLLECTION = "kb_demo"


def build_store():
    """建表 + 写入向量。pgvector 会自动建集合表，索引可后续按规模加。"""
    from langchain_postgres import PGVector   # v0.0.9+ 接口

    docs = [
        Document(page_content="RAG 通过检索外部文档再生成，减少幻觉、可溯源。",
                 metadata={"source": "kb", "topic": "rag"}),
        Document(page_content="pgvector 是 Postgres 的向量扩展，支持 ivfflat / hnsw 索引。",
                 metadata={"source": "kb", "topic": "infra"}),
        Document(page_content="Chroma 适合本地原型，生产常换 pgvector 或 Milvus。",
                 metadata={"source": "kb", "topic": "infra"}),
    ]
    store = PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION,
        connection=CONN,
        use_jsonb=True,          # metadata 存 jsonb，支持 SQL 条件过滤
    )
    store.add_documents(docs)
    print(f"已写入 {len(docs)} 条到 pgvector 集合 {COLLECTION}")
    return store


def query(store, question: str):
    """向量检索 + metadata 过滤：只查 infra 主题。
    这正是 pgvector 相对裸 Chroma 的价值——过滤条件下沉到数据库。"""
    hits = store.similarity_search(question, k=3, filter={"topic": "infra"})
    for d in hits:
        print(f"  [{d.metadata['topic']}] {d.page_content}")
    return hits


def hnsw_index_sql():
    """生产上手动建 HNSW 索引的 SQL（pgvector）。规模大了不建索引会全表扫。"""
    return (
        "-- 在 langchain_pg_embedding 表的 embedding 列建 HNSW 索引：\n"
        "CREATE INDEX ON langchain_pg_embedding "
        "USING hnsw (embedding vector_cosine_ops);"
    )


if __name__ == "__main__":
    try:
        store = build_store()
        print("\n检索（限定 infra 主题）：")
        query(store, "生产用什么向量库？")
    except Exception as e:
        print(f"未连上 pgvector（{type(e).__name__}: {e}）")
        print("先起 Postgres+pgvector 容器并 pip install langchain-postgres psycopg[binary]。")
    print("\n生产建索引 SQL：\n" + hnsw_index_sql())
    print("\n选型理由：pgvector 同库省一套运维、能 SQL 过滤；亿级再上 Milvus。")
