"""最终业务编排：安全检查、缓存、知识问答、订单查询、人工升级与观测。"""

from dataclasses import dataclass
from .assistant import SupportAnswer
from .auth import Identity
from .cache import AnswerCache
from .orders import OrderRepository
from .security import suspicious
from .tickets import TicketStore, escalate


@dataclass(frozen=True)
class ApplicationResult:
    answer: SupportAnswer
    ticket_id: str | None = None


class SupportApplication:
    def __init__(
        self,
        assistant,
        orders: OrderRepository,
        tickets: TicketStore,
        cache: AnswerCache,
    ):
        self.assistant, self.orders, self.tickets, self.cache = (
            assistant,
            orders,
            tickets,
            cache,
        )

    def handle(self, identity: Identity, question: str, version="v1", order_id=""):
        if suspicious(question):
            raise ValueError("检测到可疑指令")
        if order_id:
            order = self.orders.get_for_user(order_id, identity.user_id)
            return ApplicationResult(
                SupportAnswer(
                    f"订单 {order.order_id}：{order.status}", ("order-system",)
                )
            )
        cached = self.cache.get(identity.tenant_id, version, question)
        if cached:
            return ApplicationResult(cached)
        answer = self.assistant.ask(question)
        self.cache.put(identity.tenant_id, version, question, answer)
        ticket = escalate(
            self.tickets, identity.user_id, question, bool(answer.sources)
        )
        return ApplicationResult(answer, ticket.ticket_id if ticket else None)
