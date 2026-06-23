"""
Day 38 · 数据持久化：用 SQLite 存对话/用户
==========================================================
测试工程师转 AI 应用开发  ← 阶段4 工程化

Day28 的 checkpoint 是给"图状态"做持久化；但业务上你还要存用户、对话历史、
反馈这类结构化数据，方便查询、统计、对账。最轻量的选择是 SQLite——
一个文件就是一个库，零部署，单机/小服务足够用（量大再换 PostgreSQL）。

本节：建表、存一条问答、按用户查历史。纯 sqlite3（标准库，无需安装）。
==========================================================
"""

import sqlite3
from datetime import datetime

DB = "app.db"


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row   # 让查询结果能按列名访问
    return conn


def init_db():
    """建表。IF NOT EXISTS 保证可重复运行不报错。"""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer   TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
    print("表已就绪")


def save_qa(user_id: str, question: str, answer: str):
    """存一条问答。用参数化 (?, ?, ...) 而不是字符串拼接——防 SQL 注入，测试基本功。"""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO conversations (user_id, question, answer, created_at) VALUES (?, ?, ?, ?)",
            (user_id, question, answer, datetime.now().isoformat(timespec="seconds")),
        )
    print(f"已存：{user_id} 的一条问答")


def get_history(user_id: str, limit: int = 5):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT question, answer, created_at FROM conversations "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    save_qa("u1", "RAG 是什么", "检索增强生成")
    save_qa("u1", "FAISS 干嘛的", "向量检索库")
    save_qa("u2", "你好", "你好！")

    print("\nu1 的历史：")
    for r in get_history("u1"):
        print(f"  [{r['created_at']}] Q: {r['question']} | A: {r['answer']}")


# ----------------------------------------------------------
# 小结：
# - SQLite：单文件数据库、零部署，存用户/对话/反馈这类业务数据最省事。
# - 一定用参数化查询 (?)，不要字符串拼接 SQL——防注入，这是安全红线。
# - checkpoint（Day28）存"图状态"做恢复；业务表存"可查询的结构化数据"，两者互补。
# - 量大/要并发再迁 PostgreSQL，API 几乎一样（psycopg + 占位符换成 %s）。
#
# 动手练习：把 Day35 的 /chat 接口接上这里，每次问答都落库，再加 /history 接口查历史。
# ----------------------------------------------------------
