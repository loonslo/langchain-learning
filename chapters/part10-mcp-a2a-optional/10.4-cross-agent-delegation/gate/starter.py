"""L10 扩展 · 跨 Agent 委派 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/integration.py。实现 OrderAgent/SupportOrderDelegator，然后运行：

    python chapters/part10-mcp-a2a-optional/10.4-cross-agent-delegation/gate/gate_check.py
"""

from __future__ import annotations


class OrderAgent:
    def __init__(self, reader, context: dict):
        raise NotImplementedError("初始化订单 Agent")

    def handle(self, text: str) -> dict:
        """返回 {"state","message"}。

        - 缺订单号 -> input-required；
        - context 无 orders.read -> auth-required；
        - 否则 reader.status(...) -> completed。
        """
        raise NotImplementedError("实现订单 Agent")


class SupportOrderDelegator:
    def __init__(self, client):
        raise NotImplementedError("初始化委托器")

    def handle(self, question: str, context: dict) -> str:
        """调用 client；error -> 转人工；input-required -> 原样追问；
        auth-required -> 无权限提示；其他返回 message。"""
        raise NotImplementedError("实现委托翻译")
