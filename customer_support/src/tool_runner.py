"""只对明确的临时错误执行有限重试；权限/参数错误不重试。"""

from dataclasses import dataclass


class TransientToolError(Exception):
    """可恢复的短暂故障，例如超时或服务临时不可用。"""


class PermanentToolError(Exception):
    """重试也不会成功的故障，例如无权限或请求参数错误。"""


@dataclass(frozen=True)
class ToolResult:
    """把工具调用的成功值、实际尝试次数和失败原因放进同一返回对象。"""

    value: object | None
    attempts: int
    error: str | None = None


def call_read_only(operation, max_attempts=3):
    """执行幂等只读操作，只在 ``TransientToolError`` 时有限重试。

    只读操作重复执行通常不会改变业务数据；创建订单、退款等写操作不能直接复用此函数，
    否则响应丢失后的重试可能造成重复写入。
    """

    for attempt in range(1, max_attempts + 1):
        try:
            return ToolResult(operation(), attempts=attempt)
        except PermanentToolError as exc:
            # 永久错误立即返回；继续调用只会重复同一个失败。
            return ToolResult(None, attempts=attempt, error=str(exc))
        except TransientToolError as exc:
            # 中间轮次继续循环；最后一次仍失败才把错误交给上层处理。
            if attempt == max_attempts:
                return ToolResult(None, attempt, str(exc))
    # 正常情况下循环必定成功返回或在最后一次临时失败时返回，此行只是防御性保护。
    raise AssertionError("unreachable")
