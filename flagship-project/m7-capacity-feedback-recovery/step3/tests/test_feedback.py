from customer_support.feedback import Feedback, FeedbackStore


def test_only_negative_unreviewed_feedback_enters_queue():
    store = FeedbackStore()
    store.add(Feedback("a", -1, "引用错"))
    store.add(Feedback("b", 1, "好"))
    assert [x.trace_id for x in store.review_queue()] == ["a"]
