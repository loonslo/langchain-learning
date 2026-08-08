from customer_support.application import SupportApplication
from customer_support.assistant import SupportAnswer
from customer_support.conversation import History
from customer_support.orders import Order, OrderRepository


class Assistant:
    def ask(self, question):
        return SupportAnswer(question, ("faq.md",))


def test_order_query_is_reachable_from_the_product_application():
    app = SupportApplication(
        Assistant(),
        History(),
        OrderRepository([Order("A1", "alice", "已发货")]),
    )

    result = app.handle("查订单", user_id="alice", order_id="A1")

    assert result.answer.text == "订单 A1：已发货"
