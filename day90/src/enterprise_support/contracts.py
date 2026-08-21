"""跨模块稳定契约；业务层不依赖任意模型输出字符串。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


class Intent(StrEnum):
    REFUND_STATUS = "refund_status"
    ORDER_STATUS = "order_status"
    SHIPPING = "shipping"
    HUMAN_HANDOFF = "human_handoff"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IntentDecision:
    intent: Intent
    confidence: float
    reason: str = ""


@dataclass(frozen=True)
class SlotState:
    intent: Intent
    values: Mapping[str, str] = field(default_factory=dict)
    missing: tuple[str, ...] = ()


@dataclass(frozen=True)
class SupportReply:
    text: str
    status: str
    intent: Intent
    slots: Mapping[str, str] = field(default_factory=dict)
