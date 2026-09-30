from fastapi import FastAPI
from fastapi.testclient import TestClient

from customer_support.feedback import FeedbackStore, attach_feedback_routes


def test_feedback_enters_the_review_store_through_the_product_api():
    app = FastAPI()
    store = FeedbackStore()
    attach_feedback_routes(app, store)

    response = TestClient(app).post(
        "/feedback", json={"trace_id": "trace-1", "rating": -1, "reason": "引用错"}
    )

    assert response.status_code == 202
    assert [item.trace_id for item in store.review_queue()] == ["trace-1"]
