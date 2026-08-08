"""独立质量评测，不占用用户问答入口。"""

from __future__ import annotations
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from .assistant import REFUSAL, SupportAnswer


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
            x["id"],
            x["question"],
            tuple(x["keywords"]),
            tuple(x["sources"]),
            x["refuse"],
        )
        for x in raw
    ]


def evaluate(assistant: Assistant, cases: list[EvalCase]) -> list[dict[str, object]]:
    results = []
    for case in cases:
        actual = assistant.ask(case.question)
        answer_ok = (
            actual.text == REFUSAL
            if case.refuse
            else all(k in actual.text for k in case.keywords)
        )
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
    """供开发验收和后续 CI 调用，不进入用户问答界面。"""

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

    from .bootstrap import build_assistant
    from .settings import Settings

    settings = Settings.from_env()
    return 0 if run_evaluation(build_assistant(settings), settings.evaluation_path) else 1


if __name__ == "__main__":
    raise SystemExit(main())
