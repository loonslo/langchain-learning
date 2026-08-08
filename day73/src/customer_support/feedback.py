"""显式用户反馈进入待审数据集；不能自动修改生产 Prompt。"""

from dataclasses import dataclass

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

from .auth import AuthenticationError


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


class FeedbackRequest(BaseModel):
    trace_id: str = Field(min_length=1, max_length=100)
    rating: int
    reason: str = Field(default="", max_length=500)


def attach_feedback_routes(app, store: FeedbackStore, verifier=None) -> None:
    """把反馈接到既有 API，不创建第二套服务。"""

    @app.post("/feedback", status_code=202)
    def submit_feedback(
        request: FeedbackRequest, authorization: str = Header(default="")
    ):
        if verifier is not None:
            try:
                verifier.verify(authorization)
            except AuthenticationError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
        item = Feedback(request.trace_id, request.rating, request.reason)
        store.add(item)
        return {"accepted": True, "review_required": item.rating < 0}
