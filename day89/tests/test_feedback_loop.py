import json

from ai_testing.feedback_loop import BadCase, FeedbackQueue


def test_only_negative_feedback_enters_review_and_duplicate_is_ignored():
    queue = FeedbackQueue()
    assert queue.submit(BadCase("good", "退款", "正确", 1, "有帮助"))
    assert queue.submit(BadCase("bad", "发票", "错误", -1, "引用错"))
    assert not queue.submit(BadCase("bad", "发票", "另一个答案", -1, "重复"))

    assert [item.case_id for item in queue.review_queue()] == ["bad"]


def test_approved_bad_case_can_become_a_regression_fixture(tmp_path):
    queue = FeedbackQueue()
    queue.submit(BadCase("bad", "发票信息", "错误", -1, "缺少字段", ("faq.md",)))
    queue.approve("bad")
    output = tmp_path / "regression.json"

    assert queue.export_regression_cases(output) == 1
    assert json.loads(output.read_text(encoding="utf-8"))[0]["id"] == "bad"
    assert queue.review_queue() == []
