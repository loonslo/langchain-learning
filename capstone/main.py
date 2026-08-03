"""Capstone CLI：build / ask / eval，所有失败均返回非零退出码。"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import config as C
from .contracts import AssistRequest
from .knowledge_base import KnowledgeBase, SUPPORTED_SUFFIXES
from .permissions import User
from .security import redact, validate_question
from .service import AssistantService


def _docs_for_tenant(tenant_id: str) -> Path:
    tenant_docs = C.tenant_docs_dir(tenant_id)
    if tenant_docs.is_dir() and any(
        path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        for path in tenant_docs.rglob("*")
    ):
        return tenant_docs
    return C.DOCS_DIR


def _knowledge_base(tenant_id: str) -> KnowledgeBase:
    return KnowledgeBase(
        tenant_id=tenant_id,
        docs_dir=_docs_for_tenant(tenant_id),
        persist_dir=C.tenant_chroma_dir(tenant_id),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", default="default")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build")
    ask = subparsers.add_parser("ask")
    ask.add_argument("question", nargs="+")
    subparsers.add_parser("eval")
    args = parser.parse_args(argv)

    errors = C.validate_settings()
    if errors:
        parser.error("；".join(errors))
    kb = _knowledge_base(args.tenant)
    if args.command == "build":
        kb.build(rebuild=True)
    elif args.command == "ask":
        question = validate_question(" ".join(args.question))
        built = kb.build()

        class Registry:
            def get(self, tenant_id: str):
                if tenant_id != built.tenant_id:
                    raise PermissionError("CLI 身份与知识库租户不一致")
                return built

        service = AssistantService(Registry())
        result = service.assist(
            AssistRequest(question, request_id="cli-ask", mode="knowledge"),
            User(
                "public-reader",
                tenant_id=args.tenant,
                roles=frozenset({"public"}),
            ),
        )
        print(redact(result.answer))
    elif args.command == "eval":
        from .evaluation import run

        print("评测：", run(kb.build()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
