"""L4.12 Text2SQL 安全门 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
text2sql_agent.py。实现下面两个函数，然后运行：

    python chapters/part4-agents-langgraph/4.13-text2sql-agent/gate/gate_check.py
"""

from __future__ import annotations

DANGEROUS = {"insert", "update", "delete", "drop", "alter", "create", "pragma", "attach", "detach", "replace"}
ALLOWED_TABLES = {"sales", "conversations"}


def validate_sql(sql: str) -> None:
    """执行前安全门：SELECT 开头；危险关键字；表白名单；必须 LIMIT。

    任一不过抛 ValueError。
    """
    raise NotImplementedError("实现 SQL 安全门")


def route_question(question: str) -> str:
    """结构化指标/历史/SQL 提示 -> "text2sql"，否则 "rag"。"""
    raise NotImplementedError("实现问题分流")
