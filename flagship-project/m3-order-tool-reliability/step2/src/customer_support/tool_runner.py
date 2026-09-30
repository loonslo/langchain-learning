"""只对明确的临时错误执行有限重试；权限/参数错误不重试。"""

from dataclasses import dataclass


class TransientToolError(Exception):
    """临时错误（超时、503 等）：值得重试。"""


class PermanentToolError(Exception):
    """永久错误（参数错误、无权限等）：重试没有意义。"""


@dataclass(frozen=True)
class ToolResult:
    """工具调用结果：成功时 value 有值；失败时 error 是错误说明；attempts 是实际尝试次数。"""

    value: object | None
    attempts: int
    error: str | None = None


def call_read_only(operation, max_attempts=2):
    """调用只读工具：临时错误最多尝试 max_attempts 次，永久错误立即返回；其他异常不捕获，原样抛出。
    写操作不能用它（重试可能重复执行），要配幂等键（7.4 / step2）。
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return ToolResult(operation(), attempt)
        except PermanentToolError as exc:
            return ToolResult(None, attempt, str(exc))
        except TransientToolError as exc:
            if attempt == max_attempts:
                return ToolResult(None, attempt, str(exc))
    raise AssertionError("unreachable")
