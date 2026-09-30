from src.enterprise_support.contracts import Intent
from src.enterprise_support.slots import next_question, resolve_slots


def test_refund_requires_order_id_then_reuses_it_across_turns():
    first = resolve_slots(Intent.REFUND_STATUS, "我要查退款")
    assert first.missing == ("order_id",)
    assert next_question(first) == "请提供订单号，我再为你查询。"

    second = resolve_slots(Intent.REFUND_STATUS, "订单 A100", first.values)
    assert second.values == {"order_id": "A100"}
    assert second.missing == ()


def test_shipping_policy_question_does_not_invent_an_order_slot():
    state = resolve_slots(Intent.SHIPPING, "新疆是否包邮？")
    assert state.missing == ()
    assert state.values == {}
