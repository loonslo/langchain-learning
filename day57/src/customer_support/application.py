"""Day57 产品编排：知识问答与受控订单查询共用一个正式入口。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .assistant import SupportAnswer
from .conversation import History, Turn
from .orders import OrderRepository


class Assistant(Protocol):
    def ask(self, question: str) -> SupportAnswer: ...


@dataclass(frozen=True)
class ApplicationResult:
    answer: SupportAnswer
    ticket_id: str | None = None


class SupportApplication:
    def __init__(
        self,
        assistant: Assistant,
        history: History,
        orders: OrderRepository | None = None,
    ):
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
            order = self.orders.get_for_user(order_id, user_id)
            return ApplicationResult(
                SupportAnswer(f"订单 {order.order_id}：{order.status}", ("order-system",))
            )

        standalone = self.history.standalone(
            session_id,
            question,
            tenant_id=tenant_id,
            user_id=user_id,
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
