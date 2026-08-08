"""内容哈希驱动增量同步：新增/修改 upsert，消失文件 delete。"""

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SyncPlan:
    upsert: tuple[str, ...]
    delete: tuple[str, ...]


def scan(directory: Path):
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(directory.glob("*.md"))
    }


def plan(previous, current):
    return SyncPlan(
        tuple(x for x in current if previous.get(x) != current[x]),
        tuple(x for x in previous if x not in current),
    )


class SyncingApplication:
    """给现有产品增加同步计划能力，同时原样保留问答主链。"""

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
