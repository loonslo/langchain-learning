"""客服意图和槽位的显式状态机，可作为 LangGraph 节点逻辑的业务内核。"""

from __future__ import annotations

from typing import Protocol

from .contracts import Intent, IntentDecision, SlotState, SupportReply
from .slots import next_question, resolve_slots

MIN_CONFIDENCE = 0.75  # 低于此置信度的分类结果不进入业务分支，直接转人工


class IntentClassifier(Protocol):
    def classify(self, question: str) -> IntentDecision: ...


class ConversationState:
    """教学版内存状态；生产将它替换为带 tenant/user 边界的持久化仓储。"""

    def __init__(self) -> None:
        self._waiting: dict[str, SlotState] = {}

    def get(self, session_id: str) -> SlotState | None:
        return self._waiting.get(session_id)

    def set(self, session_id: str, state: SlotState) -> None:
        self._waiting[session_id] = state

    def clear(self, session_id: str) -> None:
        self._waiting.pop(session_id, None)


class CustomerWorkflow:
    """把分类、槽位和会话状态串成可测试的分流器。"""

    def __init__(self, classifier: IntentClassifier, state: ConversationState | None = None) -> None:
        self.classifier = classifier
        self.state = state or ConversationState()

    def handle(self, session_id: str, question: str) -> SupportReply:
        """处理一轮用户输入，返回 SupportReply。

        - 上一轮正在追问槽位时，本轮不再分类，直接当作补充信息（用户中途改变话题需要另行处理）；
        - 意图是 unknown 或置信度低于 MIN_CONFIDENCE：清理状态并转人工；
        - 必填槽位缺失：保存状态并追问第一个缺项（needs_slot）；
        - 信息齐全：清理状态并返回 ready，之后才进入订单、退款等业务能力。
        """
        pending = self.state.get(session_id)
        decision = (
            IntentDecision(pending.intent, 1.0, "补齐上轮槽位")
            if pending is not None
            else self.classifier.classify(question)
        )
        if decision.intent is Intent.UNKNOWN or decision.confidence < MIN_CONFIDENCE:
            self.state.clear(session_id)
            return SupportReply("我还不能确定你的诉求，已为你转人工确认。", "handoff", Intent.HUMAN_HANDOFF)
        if decision.intent is Intent.HUMAN_HANDOFF:
            self.state.clear(session_id)
            return SupportReply("已为你创建人工服务请求。", "handoff", decision.intent)

        slots = resolve_slots(decision.intent, question, pending.values if pending else None)
        question_for_slot = next_question(slots)
        if question_for_slot:
            self.state.set(session_id, slots)
            return SupportReply(question_for_slot, "needs_slot", decision.intent, slots.values)

        self.state.clear(session_id)
        return SupportReply("信息已齐全，正在进入受控业务处理。", "ready", decision.intent, slots.values)
