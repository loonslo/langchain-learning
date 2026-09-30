"""AI API 的流式事件和端到端响应契约测试工具。"""

from dataclasses import dataclass
import json
from typing import Any

from .contracts import validate_chat_response


@dataclass(frozen=True)
class StreamEvent:
    """一个解析后的 SSE 事件；没有 event 行时事件名为 message。"""

    event: str
    data: str
    event_id: str | None = None


def parse_sse(payload: str) -> list[StreamEvent]:
    """把 SSE 文本按空行切成事件，支持 event:、id: 和多行 data:（用换行连接）。
    没有 data 的块会被丢弃，无法识别的行（例如注释）被忽略。
    """
    events: list[StreamEvent] = []
    event_name = "message"
    data_lines: list[str] = []
    event_id: str | None = None

    def flush() -> None:
        nonlocal event_name, data_lines, event_id
        if data_lines:
            events.append(StreamEvent(event_name, "\n".join(data_lines), event_id))
        event_name, data_lines, event_id = "message", [], None

    for line in payload.splitlines():
        if not line.strip():
            flush()
        elif line.startswith("event:"):
            event_name = line[6:].strip()
        elif line.startswith("id:"):
            event_id = line[3:].strip()
        elif line.startswith("data:"):
            value = line[5:]
            # 规范只去掉冒号后的一个空格；其余空白属于数据（逐 token 输出的文本常以空格开头）
            data_lines.append(value[1:] if value.startswith(" ") else value)
    flush()
    return events


def combine_text(events: list[StreamEvent]) -> str:
    """按顺序拼接 token / message 事件的文本：data 是 JSON 对象时取 text 字段，是其他 JSON 值时转成字符串，
    不是 JSON 时原样使用；其他事件（如 done、error）忽略。本函数不判断流是否完整。
    """
    chunks: list[str] = []
    for event in events:
        if event.event in {"token", "message"}:
            try:
                value: Any = json.loads(event.data)
                chunks.append(str(value.get("text", value)) if isinstance(value, dict) else str(value))
            except json.JSONDecodeError:
                chunks.append(event.data)
    return "".join(chunks)


def validate_e2e_response(payload: dict[str, Any]) -> list[str]:
    """在 8.3 的 ChatResponse 契约上，再要求出现的 request_id 必须是字符串；返回错误列表。"""
    errors = validate_chat_response(payload)
    if payload.get("request_id") is not None and not isinstance(payload["request_id"], str):
        errors.append("request_id 必须是字符串")
    return errors
