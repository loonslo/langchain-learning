"""客服意图的槽位状态机；模型只能建议字段，业务层决定是否足够执行。"""

from __future__ import annotations

import re
from collections.abc import Mapping

from .contracts import Intent, SlotState


REQUIRED_SLOTS: dict[Intent, tuple[str, ...]] = {
    Intent.REFUND_STATUS: ("order_id",),
    Intent.ORDER_STATUS: ("order_id",),
    Intent.SHIPPING: (),
    Intent.HUMAN_HANDOFF: (),
    Intent.UNKNOWN: (),
}

SLOT_QUESTIONS = {
    "order_id": "请提供订单号，我再为你查询。",
}

_ORDER_ID = re.compile(r"(?:订单号?|order\s*(?:id)?)\s*[:：#]?\s*([A-Za-z][A-Za-z0-9_-]{1,31})", re.I)


def extract_slots(question: str) -> dict[str, str]:
    """提取确定性格式的槽位；不把猜测出的号码写入会话。"""
    match = _ORDER_ID.search(question)
    return {"order_id": match.group(1).upper()} if match else {}


def resolve_slots(
    intent: Intent,
    question: str,
    previous: Mapping[str, str] | None = None,
) -> SlotState:
    values = dict(previous or {})
    values.update(extract_slots(question))
    missing = tuple(name for name in REQUIRED_SLOTS[intent] if not values.get(name))
    return SlotState(intent=intent, values=values, missing=missing)


def next_question(state: SlotState) -> str | None:
    if not state.missing:
        return None
    return SLOT_QUESTIONS[state.missing[0]]
