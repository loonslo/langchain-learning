import pytest

from ai_testing.contracts import assert_invariants, validate_chat_response


def test_valid_chat_response_satisfies_shape_and_invariants():
    payload = {"answer": "退款需要 3–5 个工作日", "sources": ["refund.md"], "ticket_id": None}

    assert validate_chat_response(payload) == []
    assert_invariants(payload)


def test_invalid_shape_reports_all_contract_errors():
    errors = validate_chat_response({"answer": "", "sources": [1], "ticket_id": 42})

    assert len(errors) == 3


def test_refusal_cannot_claim_a_source():
    with pytest.raises(AssertionError, match="拒答不应携带"):
        assert_invariants({"answer": "知识库中没有足够信息，请转人工客服。", "sources": ["faq.md"]})
