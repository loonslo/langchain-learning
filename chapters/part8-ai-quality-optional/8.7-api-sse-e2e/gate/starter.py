"""L8 API/SSE E2E · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/api_e2e.py。实现下面三个函数，然后运行：

    python chapters/part8-ai-quality-optional/8.7-api-sse-e2e/gate/gate_check.py
"""

from __future__ import annotations


def parse_sse(payload: str) -> list[dict]:
    """解析 SSE：空行分块；event/id/data，多行 data 用换行连接；
    无 data 块丢弃；未知行（注释）忽略；无 event 名默认 message。
    返回 [{"event","data","event_id"}]。
    """
    raise NotImplementedError("实现 SSE 解析")


def combine_text(events: list[dict]) -> str:
    """只拼接 token/message 事件：data 是 JSON 对象取 text，其他 JSON 转字符串，非 JSON 原样。"""
    raise NotImplementedError("实现文本拼接")


def validate_e2e_response(payload: dict) -> list[str]:
    """在 answer/sources/ticket_id 契约上，要求 request_id 若存在必须是字符串。"""
    raise NotImplementedError("实现 E2E 校验")
