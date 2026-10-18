"""L4.3 扩展 · 节点可靠性 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
node_reliability.py。实现下面三个函数，然后运行：

    python chapters/part4-agents-langgraph/4.6-node-reliability/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable


def robust_call(fn: Callable[[], str], fallback: str) -> dict:
    """调用 fn，失败时返回降级值。

    返回 {"ok": bool, "value": str, "error": str | None}。
    要求：fn 抛任何异常都不向外抛；value=fallback，error 是可读原因。
    """
    raise NotImplementedError("实现降级调用")


def is_retryable(exc: BaseException) -> bool:
    """只把瞬时错误视为可重试：TimeoutError / ConnectionError。

    ValueError、KeyError 等确定性错误返回 False。
    """
    raise NotImplementedError("实现可重试判断")


def with_timeout(fn: Callable[[], str], seconds: float, on_timeout: str) -> str:
    """真正限时调用：超过 seconds 返回 on_timeout。

    要求：
    - seconds <= 0 -> ValueError；
    - 快速返回 -> fn 的结果；
    - 超时 -> on_timeout，不无限等待；
    - fn 抛异常 -> 原样抛出（由 robust_call 负责降级）。
    """
    raise NotImplementedError("实现超时护栏")
