"""显式用户反馈进入待审数据集；不能自动修改生产 Prompt。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Feedback:
    trace_id: str
    rating: int
    reason: str
    reviewed: bool = False


class FeedbackStore:
    def __init__(self):
        self.items = []

    def add(self, item):
        if item.rating not in (-1, 1):
            raise ValueError("rating 只能是 -1 或 1")
        self.items.append(item)

    def review_queue(self):
        return [x for x in self.items if x.rating < 0 and not x.reviewed]
