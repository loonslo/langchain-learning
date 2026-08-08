from customer_support.application import SupportApplication
from customer_support.assistant import REFUSAL, SupportAnswer
from customer_support.conversation import History
from customer_support.orders import Order, OrderRepository


class Assistant:
    def ask(self, _question):
        return SupportAnswer(REFUSAL, ())


def test_final_core_keeps_order_isolation_and_idempotent_escalation():
    app = SupportApplication(
        Assistant(),
        History(),
        OrderRepository([Order("A1", "alice", "已发货")]),
    )

    assert "已发货" in app.handle("状态", user_id="alice", order_id="A1").answer.text
    first = app.handle("未知", user_id="alice", idempotency_key="k1")
    second = app.handle("未知", user_id="alice", idempotency_key="k1")
    assert first.ticket_id == second.ticket_id
