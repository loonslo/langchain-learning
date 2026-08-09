"""验证评测规则能同时检查回答内容和引用来源。"""

import json

from src.assistant import SupportAnswer
from src.evaluation import EvalCase, evaluate, run_evaluation


class ScriptedAssistant:
    """返回固定正确答案的替身，用来聚焦测试评测器自身。"""

    def ask(self, _question):
        return SupportAnswer("退款需 3–5 个工作日", ("refund.md",))


def test_correct_text_with_wrong_citation_still_fails():
    # 回答文本通过但来源不对，整题仍须失败，避免“答得像对”却无法追溯资料。
    case = EvalCase("x", "退款", ("3–5",), ("wrong.md",), False)
    result = evaluate(ScriptedAssistant(), [case])[0]
    assert result["answer_ok"] is True and result["passed"] is False


def test_saved_evaluation_set_is_executable_from_the_product_cli(tmp_path):
    # pytest 提供的 tmp_path 是临时目录，测试结束后会自动清理。
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
