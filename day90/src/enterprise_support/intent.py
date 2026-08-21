"""意图识别的 few-shot 提示与输出契约。"""

from __future__ import annotations

import json
from typing import Any

from .contracts import Intent, IntentDecision


INTENT_FEW_SHOT_PROMPT = """你是电商客服路由器。仅输出 JSON：
{{"intent":"refund_status|order_status|shipping|human_handoff|unknown","confidence":0到1}}

示例：
用户：订单 A100 退款到哪了？
输出：{{"intent":"refund_status","confidence":0.98}}
用户：订单 B200 到哪里了？
输出：{{"intent":"order_status","confidence":0.96}}
用户：我要找人工处理投诉
输出：{{"intent":"human_handoff","confidence":0.99}}

未知或不能判断的请求一律输出 unknown，不得编造订单信息。
用户：{question}
"""


def build_intent_prompt(question: str) -> str:
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")
    return INTENT_FEW_SHOT_PROMPT.format(question=question)


def parse_intent_payload(payload: str | dict[str, Any]) -> IntentDecision:
    """校验模型 JSON；无效类别不让它进入任何业务分支。"""
    raw = json.loads(payload) if isinstance(payload, str) else payload
    if not isinstance(raw, dict):
        raise ValueError("意图输出必须是 JSON 对象")
    try:
        intent = Intent(raw["intent"])
        confidence = float(raw["confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("意图输出缺少合法 intent/confidence") from exc
    if not 0 <= confidence <= 1:
        raise ValueError("confidence 必须在 0 到 1 之间")
    return IntentDecision(intent=intent, confidence=confidence)
