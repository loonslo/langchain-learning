"""L5.9 扩展 · 意图工作流 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/workflow.py。实现 ConversationState/CustomerWorkflow，然后运行：

    python chapters/part9-enterprise-infra-optional/9.4-intent-workflow/gate/gate_check.py
"""

from __future__ import annotations

MIN_CONFIDENCE = 0.75


class ConversationState:
    """内存会话状态：get/set/clear。"""

    def get(self, session_id: str) -> dict | None:
        raise NotImplementedError("实现 get")

    def set(self, session_id: str, state: dict) -> None:
        raise NotImplementedError("实现 set")

    def clear(self, session_id: str) -> None:
        raise NotImplementedError("实现 clear")


class CustomerWorkflow:
    def __init__(self, classifier, state: ConversationState | None = None):
        raise NotImplementedError("初始化工作流")

    def handle(self, session_id: str, question: str) -> dict:
        """处理一轮，返回 {"reply","action","intent","values"}。

        - 有待补槽位：不再分类，沿用上一轮 intent；
        - unknown 或 confidence<0.75：清状态 -> handoff；
        - human_handoff：清状态 -> handoff；
        - 缺必填槽位：保存状态 -> needs_slot 并追问；
        - 齐全：清状态 -> ready。
        """
        raise NotImplementedError("实现工作流")
