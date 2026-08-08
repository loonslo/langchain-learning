"""Day75 会话存储：正式 SQLite 数据可以备份并立即验证可恢复性。"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .backup import backup, integrity


@dataclass(frozen=True)
class Message:
    role: str
    content: str


class SQLiteThreadStore:
    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS messages("
                "id INTEGER PRIMARY KEY,tenant TEXT,user TEXT,thread TEXT,"
                "role TEXT,content TEXT)"
            )

    def append(self, tenant, user, thread, message):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT INTO messages(tenant,user,thread,role,content) VALUES(?,?,?,?,?)",
                (tenant, user, thread, message.role, message.content),
            )

    def load(self, tenant, user, thread, limit=6):
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                "SELECT role,content FROM messages "
                "WHERE tenant=? AND user=? AND thread=? ORDER BY id DESC LIMIT ?",
                (tenant, user, thread, limit),
            ).fetchall()
        return [Message(*row) for row in reversed(rows)]

    def backup_to(self, target: Path) -> Path:
        """备份正式会话库，并在返回前执行 SQLite 完整性检查。"""

        backup(Path(self.path), target)
        if not integrity(target):
            raise RuntimeError("备份完整性检查失败")
        return target
