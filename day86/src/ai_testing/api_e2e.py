"""AI API 的流式事件和端到端响应契约测试工具。"""

from dataclasses import dataclass
import json
from typing import Any

from .contracts import validate_chat_response


@dataclass(frozen=True)
class StreamEvent:
    event: str
    data: str
    event_id: str | None = None


def parse_sse(payload: str) -> list[StreamEvent]:
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
            data_lines.append(line[5:].lstrip())
    flush()
    return events


def combine_text(events: list[StreamEvent]) -> str:
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
    errors = validate_chat_response(payload)
    if payload.get("request_id") is not None and not isinstance(payload["request_id"], str):
        errors.append("request_id 必须是字符串")
    return errors
