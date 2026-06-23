"""
Day 38 · Text2SQL：结构化数据问答工具分支
==========================================================
测试工程师转 AI 应用开发

RAG 适合问非结构化文档；企业里还有大量结构化数据在数据库里，比如订单、
用户、财务指标、评测运行记录。Text2SQL 分支解决的是：

自然语言问题 → 生成只读 SQL → 查询 SQLite → 把结果解释给用户

本文件重点是安全边界：
1. 只允许 SELECT
2. 只允许白名单表
3. 禁止 DELETE / UPDATE / INSERT / DROP 等危险关键字
4. 自动 LIMIT，避免一次查太多
==========================================================
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DB = "app.db"
ALLOWED_TABLES = {"sales", "conversations"}
DANGEROUS = {"insert", "update", "delete", "drop", "alter", "create", "replace", "attach", "detach", "pragma"}


@dataclass
class QueryResult:
    sql: str
    rows: list[dict]
    answer: str


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_demo_data() -> None:
    """初始化可演示的结构化数据。可重复运行。"""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                period TEXT NOT NULL,
                revenue REAL NOT NULL,
                profit REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        existing = conn.execute("SELECT COUNT(*) AS n FROM sales").fetchone()["n"]
        if existing == 0:
            conn.executemany(
                "INSERT INTO sales (company, period, revenue, profit) VALUES (?, ?, ?, ?)",
                [
                    ("示例科技", "2024Q4", 1200.0, 180.0),
                    ("示例科技", "2025Q1", 1350.0, 210.0),
                    ("示例科技", "2025Q2", 1510.0, 260.0),
                    ("远山制造", "2025Q1", 980.0, 90.0),
                    ("远山制造", "2025Q2", 1020.0, 96.0),
                ],
            )
        conv_existing = conn.execute("SELECT COUNT(*) AS n FROM conversations").fetchone()["n"]
        if conv_existing == 0:
            conn.executemany(
                "INSERT INTO conversations (user_id, question, answer, created_at) VALUES (?, ?, ?, ?)",
                [
                    ("u1", "RAG 是什么", "检索增强生成", "2026-06-23T09:00:00"),
                    ("u1", "FAISS 干什么", "向量相似度检索", "2026-06-23T09:05:00"),
                    ("u2", "你好", "你好，我是知识库助手。", "2026-06-23T09:10:00"),
                ],
            )


def generate_sql(question: str) -> str:
    """
    教学版用规则模拟 Text2SQL，避免一上来把安全性交给模型。
    真实项目可把这里替换成 LLM 生成 SQL，但 validate_sql 必须保留。
    """
    q = question.lower()
    company = "示例科技" if "示例科技" in question else "远山制造" if "远山制造" in question else None

    if "历史" in question or "对话" in question:
        user = re.search(r"u\d+", question)
        user_id = user.group(0) if user else "u1"
        return (
            "SELECT question, answer, created_at FROM conversations "
            f"WHERE user_id = '{user_id}' ORDER BY created_at DESC LIMIT 5"
        )

    metric = "profit" if ("利润" in question or "profit" in q) else "revenue"
    columns = f"company, period, {metric}"

    if "最新" in question or "最近" in question:
        where = f"WHERE company = '{company}' " if company else ""
        return f"SELECT {columns} FROM sales {where}ORDER BY period DESC LIMIT 1"

    if "增长" in question or "趋势" in question:
        where = f"WHERE company = '{company}' " if company else ""
        return f"SELECT {columns} FROM sales {where}ORDER BY period ASC LIMIT 8"

    where = f"WHERE company = '{company}' " if company else ""
    return f"SELECT {columns} FROM sales {where}ORDER BY period DESC LIMIT 5"


def validate_sql(sql: str) -> None:
    compact = " ".join(sql.strip().split())
    lowered = compact.lower()
    if not lowered.startswith("select "):
        raise ValueError("只允许 SELECT 查询")
    tokens = set(re.findall(r"\b[a-z_]+\b", lowered))
    if tokens & DANGEROUS:
        raise ValueError("SQL 含危险关键字")

    tables = set(re.findall(r"\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)|\bjoin\s+([a-zA-Z_][a-zA-Z0-9_]*)", lowered))
    flattened = {name for pair in tables for name in pair if name}
    if not flattened:
        raise ValueError("未识别到查询表")
    if not flattened <= ALLOWED_TABLES:
        raise ValueError(f"表不在白名单内：{flattened - ALLOWED_TABLES}")
    if " limit " not in lowered:
        raise ValueError("必须带 LIMIT，避免大查询")


def execute_sql(sql: str) -> list[dict]:
    validate_sql(sql)
    with get_conn() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def explain_result(question: str, sql: str, rows: list[dict]) -> str:
    if not rows:
        return f"没有查到结果。SQL: {sql}"
    if len(rows) == 1:
        return f"根据结构化数据查询，结果是：{rows[0]}。SQL: {sql}"
    return f"根据结构化数据查询，共 {len(rows)} 条：{rows}。SQL: {sql}"


def text2sql_answer(question: str) -> QueryResult:
    sql = generate_sql(question)
    rows = execute_sql(sql)
    return QueryResult(sql=sql, rows=rows, answer=explain_result(question, sql, rows))


def route_question(question: str) -> str:
    """最小分流：结构化指标/历史记录走 Text2SQL，其他问题交给 RAG。"""
    structured_hints = ["营收", "收入", "利润", "最新", "增长", "趋势", "历史对话", "数据库", "sql"]
    return "text2sql" if any(h in question.lower() for h in structured_hints) else "rag"


if __name__ == "__main__":
    init_demo_data()
    for q in [
        "示例科技最新一期营收是多少？",
        "远山制造利润趋势如何？",
        "查询 u1 的历史对话",
        "RAG 是什么？",
    ]:
        route = route_question(q)
        print(f"\nQ: {q}\nroute: {route}")
        if route == "text2sql":
            print(text2sql_answer(q).answer)
        else:
            print("交给 RAG 分支处理。")


# ----------------------------------------------------------
# 小结：
# - RAG 问文档，Text2SQL 问表。Agent 的价值是按问题自动分流。
# - 只读连接、白名单表、SELECT-only、LIMIT 是 Text2SQL 的安全底线。
# - 真实项目里可以让 LLM 生成 SQL，但执行前必须保留 validate_sql 这道门。
# ----------------------------------------------------------
