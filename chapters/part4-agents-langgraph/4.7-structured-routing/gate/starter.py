"""L4.5 结构化路由 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
structured_routing.py。实现下面三个函数，然后运行：

    python chapters/part4-agents-langgraph/4.7-structured-routing/gate/gate_check.py
"""

from __future__ import annotations


def parse_route(text: str, allowed: set[str]) -> str:
    """解析 {"next": "...", "reason": "..."} 并校验 next 在 allowed 内。

    要求：
    - 非字符串/非法 JSON/缺 next/next 不在 allowed -> ValueError；
    - 返回 next。
    """
    raise NotImplementedError("实现结构化路由解析")


def route_next(state: dict) -> str:
    """done=True 返回 "end"，否则返回 state["_next"]；_next 非法 -> ValueError。"""
    raise NotImplementedError("实现路由函数")


def parse_intent(text: str) -> str:
    """解析 {"category": "..."}；只允许 knowledge/data_query/chitchat。"""
    raise NotImplementedError("实现意图解析")
