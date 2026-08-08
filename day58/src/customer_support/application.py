"""Day58 产品编排：订单读取进入有限重试，永久错误仍立即失败。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .assistant import SupportAnswer
from .conversation import History, Turn
from .orders import OrderRepository
from .tool_runner import call_read_only


class Assistant(Protocol):
    def ask(self, question: str) -> SupportAnswer: ...


@dataclass(frozen=True)
class ApplicationResult:
    answer: SupportAnswer
    ticket_id: str | None = None


class SupportApplication:
    def __init__(self, assistant: Assistant, history: History, orders=None):
        self.assistant = assistant
        self.history = history
        self.orders = orders or OrderRepository([])

    def handle(
        self,
        question: str,
        *,
        session_id: str = "cli",
        tenant_id: str = "local",
        user_id: str = "local",
        order_id: str = "",
    ) -> ApplicationResult:
        if order_id:
            tool_result = call_read_only(
                lambda: self.orders.get_for_user(order_id, user_id),
                max_attempts=2,
            )
            if tool_result.error:
                return ApplicationResult(SupportAnswer("订单系统暂时不可用，请稍后重试。", ()))
            order = tool_result.value
            return ApplicationResult(
                SupportAnswer(f"订单 {order.order_id}：{order.status}", ("order-system",))
            )

        standalone = self.history.standalone(
            session_id, question, tenant_id=tenant_id, user_id=user_id
        )
        answer = self.assistant.ask(standalone)
        self.history.add(
            session_id,
            Turn(question, answer.text),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        return ApplicationResult(answer)

    def ask(self, question: str, **kwargs) -> SupportAnswer:
        return self.handle(question, **kwargs).answer
