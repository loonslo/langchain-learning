"""SQLite 备份与恢复验证：存在备份文件不等于可以恢复。"""

import sqlite3
from pathlib import Path


def backup(source: Path, target: Path):
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        src.backup(dst)


def integrity(path: Path) -> bool:
    with sqlite3.connect(path) as c:
        return c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
