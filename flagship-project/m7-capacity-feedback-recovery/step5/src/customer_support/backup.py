"""SQLite 备份与恢复验证：存在备份文件不等于可以恢复。"""

import sqlite3
from pathlib import Path


def backup(source: Path, target: Path):
    """用 SQLite 在线备份接口把 source 复制到 target。"""
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        src.backup(dst)


def integrity(path: Path) -> bool:
    """对文件执行 PRAGMA integrity_check，返回结果是否为 ok。"""
    with sqlite3.connect(path) as c:
        return c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
