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
    """分类结果：意图枚举和 0–1 的置信度。"""

    intent: Intent
    confidence: float
    reason: str = ""


@dataclass(frozen=True)
class SlotState:
    """槽位状态：values 是已获得的值，missing 是仍缺少的必填槽位。"""

    intent: Intent
    values: Mapping[str, str] = field(default_factory=dict)
    missing: tuple[str, ...] = ()


@dataclass(frozen=True)
class SupportReply:
    """工作流的回复：status 是 needs_slot（追问）、ready（信息齐全）或 handoff（转人工）。"""

    text: str
    status: str
    intent: Intent
    slots: Mapping[str, str] = field(default_factory=dict)
