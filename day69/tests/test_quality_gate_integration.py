import json

from customer_support.assistant import SupportAnswer
from customer_support.evaluation import run_quality_gate


class Assistant:
    def ask(self, _question):
        return SupportAnswer("错误答案", ())


def test_evaluation_result_reaches_the_release_gate(tmp_path):
    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            [
                {
                    "id": "refund",
                    "question": "退款",
                    "keywords": ["3–5"],
                    "sources": ["refund.md"],
                    "refuse": False,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert run_quality_gate(Assistant(), cases) is False
