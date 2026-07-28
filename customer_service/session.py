"""
customer_service/session.py · 会话持久化：多轮对话历史存 SQLite（复用 Day44）
==========================================================
客服和知识库问答的核心差异之一：客服是多轮的。
"我的订单到哪了" → "就是昨天那个" 需要上文才能懂。
这里存两样：消息历史（喂给 LLM 当上下文）+ 工单（转人工的落点）。
==========================================================
"""

import sqlite3
from datetime import datetime

import config as C


def get_conn():
    conn = sqlite3.connect(C.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,          -- user / assistant
                content TEXT NOT NULL,
                intent TEXT,
                created_at TEXT NOT NULL
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL
            )""")


def append(session_id: str, role: str, content: str, intent: str | None = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, intent, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, intent, datetime.now().isoformat(timespec="seconds")),
        )


def history(session_id: str, limit: int = 10) -> list[dict]:
    """最近 limit 条消息（时间正序），拼进 prompt 当多轮上下文。"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id=? "
            "ORDER BY id DESC LIMIT ?", (session_id, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def create_ticket(session_id: str, summary: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tickets (session_id, summary, created_at) VALUES (?, ?, ?)",
            (session_id, summary, datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid
