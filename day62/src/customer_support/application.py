"""Day62 产品编排：可能创建工单的写路径使用幂等键去重。"""

from __future__ import annotations

from dataclasses import dataclass

from .assistant import SupportAnswer
from .conversation import History, Turn
from .idempotency import IdempotencyStore
from .orders import OrderRepository
from .tickets import TicketStore, escalate
from .tool_runner import call_read_only


@dataclass(frozen=True)
class ApplicationResult:
    answer: SupportAnswer
    ticket_id: str | None = None


class SupportApplication:
    def __init__(
        self,
        assistant,
        history: History,
        orders=None,
        tickets=None,
        idempotency=None,
    ):
        self.assistant = assistant
        self.history = history
        self.orders = orders or OrderRepository([])
        self.tickets = tickets or TicketStore()
        self.idempotency = idempotency or IdempotencyStore()

    def handle(
        self,
        question: str,
        *,
        session_id: str = "cli",
        tenant_id: str = "local",
        user_id: str = "local",
        order_id: str = "",
        idempotency_key: str = "",
    ) -> ApplicationResult:
        if order_id:
            tool_result = call_read_only(
                lambda: self.orders.get_for_user(order_id, user_id), max_attempts=2
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

        create_ticket = lambda: escalate(
            self.tickets, user_id, question, bool(answer.sources)
        )
        ticket = (
            self.idempotency.execute(
                idempotency_key,
                {"tenant": tenant_id, "user": user_id, "question": question},
                create_ticket,
            )
            if idempotency_key
            else create_ticket()
        )
        return ApplicationResult(answer, ticket.ticket_id if ticket else None)

    def ask(self, question: str, **kwargs) -> SupportAnswer:
        return self.handle(question, **kwargs).answer
