from customer_support.application import SupportApplication
from customer_support.assistant import SupportAnswer
from customer_support.conversation import History
from customer_support.orders import Order
from customer_support.tool_runner import TransientToolError


class Assistant:
    def ask(self, question):
        return SupportAnswer(question, ())


class FlakyOrders:
    def __init__(self):
        self.calls = 0

    def get_for_user(self, order_id, user_id):
        self.calls += 1
        if self.calls == 1:
            raise TransientToolError("503")
        return Order(order_id, user_id, "已发货")


def test_product_order_path_uses_the_read_only_retry_policy():
    orders = FlakyOrders()
    app = SupportApplication(Assistant(), History(), orders)

    assert "已发货" in app.handle("查订单", order_id="A1").answer.text
    assert orders.calls == 2
