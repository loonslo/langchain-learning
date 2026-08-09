"""独立质量评测，不占用用户问答入口。

评测相当于给客服助手出一套固定试题：每题既检查回答中是否含必要关键词，
也检查引用是否来自期望的资料。它用于开发验收，不会在用户提问时自动执行。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.assistant import REFUSAL, SupportAnswer
from src.bootstrap import build_assistant
from src.settings import Settings


class Assistant(Protocol):
    """评测所需的最小能力；真实助手或测试脚本助手都可实现它。"""

    def ask(self, question: str) -> SupportAnswer: ...


@dataclass(frozen=True)
class EvalCase:
    """一条可重复运行的评测用例及其判定标准。"""

    id: str
    question: str
    keywords: tuple[str, ...]
    sources: tuple[str, ...]
    refuse: bool


def load_cases(path: Path) -> list[EvalCase]:
    """从 JSON 文件读取评测题，并转换为带类型提示的 ``EvalCase`` 对象。"""
    if not path.is_file():
        raise FileNotFoundError(f"评测集不存在：{path}")
    # ``json.loads`` 把文本格式的 JSON 转为 Python 的列表和字典。
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not raw:
        raise ValueError("评测集不能为空")
    return [
        EvalCase(
            item["id"],
            item["question"],
            tuple(item["keywords"]),
            tuple(item["sources"]),
            item["refuse"],
        )
        for item in raw
    ]


def evaluate(assistant: Assistant, cases: list[EvalCase]) -> list[dict[str, object]]:
    """逐题调用助手并返回可保存、可展示的评测明细，不直接打印结果。"""
    results = []
    for case in cases:
        actual = assistant.ask(case.question)
        # 拒答题必须精确匹配拒答文案；普通题要求所有关键字都出现在回答中。
        answer_ok = (
            actual.text == REFUSAL
            if case.refuse
            else all(keyword in actual.text for keyword in case.keywords)
        )
        # 转成 set 后不受来源顺序影响，但仍能检查是否缺了或多了来源。
        citation_ok = set(actual.sources) == set(case.sources)
        results.append(
            {
                "id": case.id,
                "question": case.question,
                "answer": actual.text,
                "sources": list(actual.sources),
                "answer_ok": answer_ok,
                "citation_ok": citation_ok,
                "passed": answer_ok and citation_ok,
            }
        )
    return results


def run_evaluation(
    assistant: Assistant,
    cases_path: Path,
    output: Callable[[str], None] = print,
) -> bool:
    """供开发验收和后续 CI 调用，不进入用户问答界面。

    CI 是持续集成：每次修改代码后由自动化环境重复运行检查，尽早发现回归问题。
    """

    results = evaluate(assistant, load_cases(cases_path))
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        output(
            f"[{status}] {result['id']} | answer={result['answer_ok']} "
            f"citation={result['citation_ok']} | {result['answer']}"
        )
    passed = sum(bool(result["passed"]) for result in results)
    output(f"评测结果：{passed}/{len(results)} 通过")
    return passed == len(results)


def main() -> int:
    """用真实产品依赖运行固定回归集。"""
    settings = Settings.from_env()
    return 0 if run_evaluation(build_assistant(settings), settings.evaluation_path) else 1


if __name__ == "__main__":
    raise SystemExit(main())
