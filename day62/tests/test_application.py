from customer_support.application import SupportApplication
from customer_support.assistant import REFUSAL, SupportAnswer
from customer_support.conversation import History


class Assistant:
    def ask(self, _question):
        return SupportAnswer(REFUSAL, ())


def test_retried_product_request_reuses_the_same_ticket():
    app = SupportApplication(Assistant(), History())
    first = app.handle("未知", user_id="alice", idempotency_key="k1")
    second = app.handle("未知", user_id="alice", idempotency_key="k1")

    assert first.ticket_id == second.ticket_id
    assert len(app.tickets.items) == 1
