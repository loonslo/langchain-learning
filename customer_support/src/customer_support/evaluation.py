import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from dill import citation

from src.customer_support.assistant import SupportAnswer, REFUSAL


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
        ) for x in raw
    ]

def evaluate(assistant: Assistant, cases: list[EvalCase]) -> list[dict[str,object]]:
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
                "answer_ok": answer_ok,
                "citation_ok": citation_ok,
                "passed": answer_ok and citation_ok,
            }
        )
    return results