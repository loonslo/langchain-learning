"""Day71 增量同步：计划通过 VectorStore 契约真正执行，而不是只打印列表。"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document

from .vector_store import VectorStore


@dataclass(frozen=True)
class SyncPlan:
    upsert: tuple[str, ...]
    delete: tuple[str, ...]


def scan(directory: Path):
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.glob("*.md"))
    }


def plan(previous, current):
    return SyncPlan(
        tuple(name for name in current if previous.get(name) != current[name]),
        tuple(name for name in previous if name not in current),
    )


def apply_plan(
    store: VectorStore,
    sync_plan: SyncPlan,
    documents_by_source: dict[str, list[Document]],
) -> None:
    """先删除消失来源，再 upsert 新增/变化来源；具体数据库由适配器决定。"""

    for source_id in sync_plan.delete:
        store.delete_source(source_id)
    documents = [
        document
        for source_id in sync_plan.upsert
        for document in documents_by_source.get(source_id, ())
    ]
    if documents:
        store.upsert(documents)


class SyncingApplication:
    def __init__(self, application, knowledge_path: Path):
        self.application = application
        self.knowledge_path = knowledge_path

    def handle(self, *args, **kwargs):
        return self.application.handle(*args, **kwargs)

    def ask(self, *args, **kwargs):
        return self.application.ask(*args, **kwargs)

    def plan_sync(self, previous: dict[str, str]) -> SyncPlan:
        return plan(previous, scan(self.knowledge_path))

    def __getattr__(self, name):
        return getattr(self.application, name)
