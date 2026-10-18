"""L5.2 可靠性 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
reliability.py。实现下面三个函数，然后运行：

    python chapters/part5-production/5.2-reliability-retry/gate/gate_check.py
"""

from __future__ import annotations


def backoff_delays(max_retries: int, base: float = 1.0, max_delay: float = 20.0) -> list[float]:
    """指数退避等待序列：base, 2*base, 4*base...，每项不超过 max_delay。

    要求：
    - max_retries < 0 -> ValueError；
    - base <= 0 或 max_delay <= 0 -> ValueError；
    - max_retries=0 -> []。
    """
    raise NotImplementedError("实现指数退避")


def is_retryable(exc: BaseException) -> bool:
    """只把瞬时错误视为可重试：TimeoutError / ConnectionError。

    ValueError、KeyError、PermissionError 返回 False。
    """
    raise NotImplementedError("实现可重试判断")


def estimate_cost(usage: dict | None, price_per_1k: float) -> float:
    """按 total_tokens / 1000 * price_per_1k 估算成本。

    - usage 为 None/缺 total_tokens -> 0.0；
    - price_per_1k < 0 -> ValueError。
    """
    raise NotImplementedError("实现成本估算")
