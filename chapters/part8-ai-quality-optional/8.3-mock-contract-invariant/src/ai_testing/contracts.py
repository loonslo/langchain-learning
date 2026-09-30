"""API、模型回答和工具轨迹的契约与不变量检查。"""

from collections.abc import Mapping
from typing import Any


def validate_chat_response(payload: Mapping[str, Any]) -> list[str]:
    """返回所有契约错误；不在这里抛异常，便于 CI 一次报告完整问题。"""

    errors: list[str] = []
    if not isinstance(payload.get("answer"), str) or not payload["answer"].strip():
        errors.append("answer 必须是非空字符串")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, str) and item for item in sources):
        errors.append("sources 必须是字符串列表")
    if "ticket_id" in payload and payload["ticket_id"] is not None and not isinstance(
        payload["ticket_id"], str
    ):
        errors.append("ticket_id 必须是字符串或 null")
    return errors


def assert_invariants(payload: Mapping[str, Any]) -> None:
    """在契约之上检查业务不变量，任一不满足就抛 AssertionError：
    1. 拒答（答案含“没有足够信息”，旗舰后端的拒答话术）不能带知识来源；
    2. 有工单号但没有来源时，答案必须说明转人工。
    """
    errors = validate_chat_response(payload)
    if errors:
        raise AssertionError("; ".join(errors))

    answer = str(payload["answer"])
    sources = payload["sources"]
    if "没有足够信息" in answer and sources:
        raise AssertionError("拒答不应携带知识来源")
    if payload.get("ticket_id") and "人工" not in answer and not sources:
        raise AssertionError("无来源工单结果必须明确告知人工升级")
