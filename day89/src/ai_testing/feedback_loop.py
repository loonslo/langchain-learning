"""把线上 bad case 送入人工审查和回归集，禁止未经审核污染生产评测。"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class BadCase:
    case_id: str
    question: str
    answer: str
    rating: int
    reason: str
    sources: tuple[str, ...] = ()
    status: str = "pending"

    def __post_init__(self) -> None:
        if self.rating not in (-1, 1):
            raise ValueError("rating 只能是 -1 或 1")
        if not self.question.strip() or not self.case_id.strip():
            raise ValueError("case_id 和 question 不能为空")


class FeedbackQueue:
    def __init__(self) -> None:
        self._items: dict[str, BadCase] = {}

    def submit(self, item: BadCase) -> bool:
        """返回是否新入队；重复 case 不重复污染审查队列。"""

        if item.case_id in self._items:
            return False
        self._items[item.case_id] = item
        return True

    def review_queue(self) -> list[BadCase]:
        return [item for item in self._items.values() if item.rating < 0 and item.status == "pending"]

    def approve(self, case_id: str) -> BadCase:
        item = self._items[case_id]
        approved = BadCase(
            item.case_id,
            item.question,
            item.answer,
            item.rating,
            item.reason,
            item.sources,
            status="approved",
        )
        self._items[case_id] = approved
        return approved

    def export_regression_cases(self, path: Path) -> int:
        cases = [
            {
                "id": item.case_id,
                "question": item.question,
                "answer": item.answer,
                "sources": list(item.sources),
                "reason": item.reason,
            }
            for item in self._items.values()
            if item.status == "approved"
        ]
        path.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
        return len(cases)
