"""L5.4 数据持久化 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
sqlite_persistence.py。实现下面四个函数，然后运行：

    python chapters/part5-production/5.4-sqlite-persistence/gate/gate_check.py
"""

from __future__ import annotations

from pathlib import Path


def init_db(path: str | Path) -> int:
    """建表并返回 schema 版本（固定为 1）。

    要求：
    - conversations 表：id/trace_id(唯一)/user_id/session_id/question/answer/
      model/prompt_tokens/completion_tokens/cost_usd/latency_ms/status/error/
      sources/created_at；
    - feedback 表：id/conversation_id/rating/comment/created_at；
    - created_at 存 UTC ISO8601；
    - 幂等：重复调用不报错。
    """
    raise NotImplementedError("实现建表")


def save_qa(path, trace_id: str, user_id: str, question: str, answer: str) -> int:
    """落一条问答，返回主键；trace_id 重复时返回已有 id（幂等）。"""
    raise NotImplementedError("实现写入")


def get_history(path, user_id: str, limit: int = 20, before_id: int | None = None) -> list[dict]:
    """按 id 倒序返回用户历史；before_id 游标分页；sources 还原成 list。"""
    raise NotImplementedError("实现历史查询")


def save_feedback(path, conversation_id: int, rating: int, comment: str | None = None) -> int:
    """写反馈；rating 只能是 1/-1；不存在的会话 id -> ValueError。"""
    raise NotImplementedError("实现反馈写入")
