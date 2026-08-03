"""只对明确的临时错误执行有限重试；权限/参数错误不重试。"""

from dataclasses import dataclass


class TransientToolError(Exception):
    pass


class PermanentToolError(Exception):
    pass


@dataclass(frozen=True)
class ToolResult:
    value: object | None
    attempts: int
    error: str | None = None


def call_read_only(operation, max_attempts=2):
    for attempt in range(1, max_attempts + 1):
        try:
            return ToolResult(operation(), attempt)
        except PermanentToolError as exc:
            return ToolResult(None, attempt, str(exc))
        except TransientToolError as exc:
            if attempt == max_attempts:
                return ToolResult(None, attempt, str(exc))
    raise AssertionError("unreachable")
