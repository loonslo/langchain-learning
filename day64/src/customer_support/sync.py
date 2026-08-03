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
