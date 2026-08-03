from customer_support.assistant import SupportAnswer
from customer_support.evaluation import EvalCase, evaluate


class FakeAssistant:
    def ask(self, _q):
        return SupportAnswer("退款需 3–5 个工作日", ("refund.md",))


def test_correct_text_with_wrong_citation_still_fails():
    case = EvalCase("x", "退款", ("3–5",), ("wrong.md",), False)
    result = evaluate(FakeAssistant(), [case])[0]
    assert result["answer_ok"] is True and result["passed"] is False
