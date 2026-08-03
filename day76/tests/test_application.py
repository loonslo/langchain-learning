from customer_support.application import SupportApplication
from customer_support.assistant import REFUSAL, SupportAnswer
from customer_support.auth import Identity
from customer_support.cache import AnswerCache
from customer_support.orders import Order, OrderRepository
from customer_support.tickets import TicketStore


class A:
    def ask(self, q):
        return SupportAnswer(REFUSAL, ())


def test_end_to_end_order_is_scoped_and_unknown_question_escalates():
    app = SupportApplication(
        A(),
        OrderRepository([Order("A1", "alice", "已发货")]),
        TicketStore(),
        AnswerCache(60, lambda: 0),
    )
    assert (
        "已发货"
        in app.handle(Identity("shop", "alice"), "状态", order_id="A1").answer.text
    )
    assert app.handle(Identity("shop", "alice"), "未知权益").ticket_id
