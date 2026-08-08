from customer_support.application import SupportApplication
from customer_support.assistant import REFUSAL, SupportAnswer
from customer_support.conversation import History


class Assistant:
    def ask(self, _question):
        return SupportAnswer(REFUSAL, ())


def test_refusal_creates_a_ticket_on_the_real_product_path():
    result = SupportApplication(Assistant(), History()).handle("未知会员权益", user_id="alice")

    assert result.answer.text == REFUSAL
    assert result.ticket_id
