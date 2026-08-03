"""SQLite 会话存储：租户、用户和线程共同构成读取边界。"""

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    role: str
    content: str


class SQLiteThreadStore:
    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as c:
            c.execute(
                "CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,tenant TEXT,user TEXT,thread TEXT,role TEXT,content TEXT)"
            )

    def append(self, tenant, user, thread, message):
        with sqlite3.connect(self.path) as c:
            c.execute(
                "INSERT INTO messages(tenant,user,thread,role,content) VALUES(?,?,?,?,?)",
                (tenant, user, thread, message.role, message.content),
            )

    def load(self, tenant, user, thread, limit=6):
        with sqlite3.connect(self.path) as c:
            rows = c.execute(
                "SELECT role,content FROM messages WHERE tenant=? AND user=? AND thread=? ORDER BY id DESC LIMIT ?",
                (tenant, user, thread, limit),
            ).fetchall()
        return [Message(*x) for x in reversed(rows)]
