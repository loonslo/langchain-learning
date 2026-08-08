from customer_support.assistant import SupportAnswer
import json

from customer_support.evaluation import EvalCase, evaluate, run_evaluation


class ScriptedAssistant:
    def ask(self, _q):
        return SupportAnswer("退款需 3–5 个工作日", ("refund.md",))


def test_correct_text_with_wrong_citation_still_fails():
    case = EvalCase("x", "退款", ("3–5",), ("wrong.md",), False)
    result = evaluate(ScriptedAssistant(), [case])[0]
    assert result["answer_ok"] is True and result["passed"] is False


def test_saved_evaluation_set_is_executable_from_the_product_cli(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "refund",
                    "question": "退款多久到账？",
                    "keywords": ["3–5"],
                    "sources": ["refund.md"],
                    "refuse": False,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    output = []

    assert run_evaluation(ScriptedAssistant(), path, output.append)
    assert output[-1] == "评测结果：1/1 通过"
