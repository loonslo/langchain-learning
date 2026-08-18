import pytest

from src.enterprise_support.contracts import Intent
from src.enterprise_support.intent import build_intent_prompt, parse_intent_payload


def test_few_shot_prompt_requires_unknown_fallback():
    prompt = build_intent_prompt("帮我看下 A100 的退款")
    assert "unknown" in prompt
    assert "A100" in prompt


def test_intent_payload_is_constrained_to_business_enum():
    decision = parse_intent_payload('{"intent":"refund_status","confidence":0.9}')
    assert decision.intent is Intent.REFUND_STATUS


@pytest.mark.parametrize(
    "payload",
    [
        '{"intent":"make_payment","confidence":0.9}',
        '{"intent":"shipping","confidence":1.1}',
        '{"intent":"shipping"}',
    ],
)
def test_invalid_model_routing_cannot_reach_business_branch(payload):
    with pytest.raises(ValueError):
        parse_intent_payload(payload)
