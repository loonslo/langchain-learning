"""把线上 bad case 送入人工审查和回归集，禁止未经审核污染生产评测。"""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class BadCase:
    """一条线上反馈。rating 是 -1（点踩）或 1（点赞）；answer 是线上给出的回答（可能有问题），不是标准答案；
    status 经人工审核从 pending 变为 approved。
    """

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
    """反馈队列：去重、人工审核、导出回归样本。"""

    def __init__(self) -> None:
        self._items: dict[str, BadCase] = {}

    def submit(self, item: BadCase) -> bool:
        """返回是否新入队；重复 case 不重复污染审查队列。"""

        if item.case_id in self._items:
            return False
        self._items[item.case_id] = item
        return True

    def review_queue(self) -> list[BadCase]:
        """返回等待审核的负反馈（rating < 0 且状态为 pending）。"""
        return [item for item in self._items.values() if item.rating < 0 and item.status == "pending"]

    def approve(self, case_id: str) -> BadCase:
        """人工审核通过，状态改为 approved；case_id 不存在会抛 KeyError。本章不记录预期答案，导出后由审核者补写。"""
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
        """把已批准的案例写成 JSON 并返回数量。导出内容含线上的错误回答（answer）和来源，但没有预期结果，
        补上预期后才能作为回归断言。
        """
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
