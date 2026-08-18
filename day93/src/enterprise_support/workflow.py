"""客服意图和槽位的显式状态机，可作为 LangGraph 节点逻辑的业务内核。"""

from __future__ import annotations

from typing import Protocol

from .contracts import Intent, IntentDecision, SlotState, SupportReply
from .slots import next_question, resolve_slots


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
    def __init__(self, classifier: IntentClassifier, state: ConversationState | None = None) -> None:
        self.classifier = classifier
        self.state = state or ConversationState()

    def handle(self, session_id: str, question: str) -> SupportReply:
        pending = self.state.get(session_id)
        decision = (
            IntentDecision(pending.intent, 1.0, "补齐上轮槽位")
            if pending is not None
            else self.classifier.classify(question)
        )
        if decision.intent is Intent.UNKNOWN or decision.confidence < 0.75:
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
