"""Day69 评测入口：生成指标后立即经过质量门，而不是只打印报告。"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .assistant import REFUSAL, SupportAnswer
from .quality_gate import check


class Assistant(Protocol):
    def ask(self, question: str) -> SupportAnswer: ...


@dataclass(frozen=True)
class EvalCase:
    id: str
    question: str
    keywords: tuple[str, ...]
    sources: tuple[str, ...]
    refuse: bool


def load_cases(path: Path) -> list[EvalCase]:
    if not path.is_file():
        raise FileNotFoundError(f"评测集不存在：{path}")
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
    results = []
    for case in cases:
        actual = assistant.ask(case.question)
        answer_ok = (
            actual.text == REFUSAL
            if case.refuse
            else all(keyword in actual.text for keyword in case.keywords)
        )
        citation_ok = set(actual.sources) == set(case.sources)
        results.append(
            {
                "id": case.id,
                "question": case.question,
                "answer": actual.text,
                "sources": list(actual.sources),
                "refuse": case.refuse,
                "answer_ok": answer_ok,
                "citation_ok": citation_ok,
                "passed": answer_ok and citation_ok,
            }
        )
    return results


def metrics_from_results(results: list[dict[str, object]]) -> dict[str, float]:
    if not results:
        raise ValueError("评测结果不能为空")
    refusal = [result for result in results if result["refuse"]]
    return {
        "pass_rate": sum(bool(result["passed"]) for result in results) / len(results),
        "citation_rate": sum(bool(result["citation_ok"]) for result in results)
        / len(results),
        "refusal_rate": (
            sum(bool(result["answer_ok"]) for result in refusal) / len(refusal)
            if refusal
            else 1.0
        ),
    }


def run_evaluation(
    assistant: Assistant,
    cases_path: Path,
    output: Callable[[str], None] = print,
) -> bool:
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


def run_quality_gate(
    assistant: Assistant,
    cases_path: Path,
    output: Callable[[str], None] = print,
) -> bool:
    results = evaluate(assistant, load_cases(cases_path))
    metrics = metrics_from_results(results)
    failures = check(metrics)
    output(f"质量指标：{metrics}")
    for failure in failures:
        output(f"GATE FAIL: {failure}")
    return not failures


def main() -> int:
    from .bootstrap import build_assistant
    from .settings import Settings

    settings = Settings.from_env()
    return 0 if run_quality_gate(build_assistant(settings), settings.evaluation_path) else 1


if __name__ == "__main__":
    raise SystemExit(main())
