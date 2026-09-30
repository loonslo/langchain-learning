"""从压测样本计算 p95、错误率和是否满足容量目标。"""

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class CapacityReport:
    p95_ms: float
    error_rate: float
    passed: bool


def report(latencies, statuses, p95_limit=2000, error_limit=0.01):
    """p95 取升序后第 ceil(0.95 × n) 个样本（nearest-rank），小样本也不会丢掉最慢的请求。

    错误率是状态码 ≥ 500 的比例；p95 和错误率都不超过目标才算通过。
    样本为空时抛 ValueError，不会默认通过。
    """
    if not latencies or not statuses:
        raise ValueError("压测样本不能为空")
    ordered = sorted(latencies)
    index = min(len(ordered) - 1, max(0, ceil(len(ordered) * 0.95) - 1))
    p95 = ordered[index]
    errors = sum(x >= 500 for x in statuses) / len(statuses)
    return CapacityReport(p95, errors, p95 <= p95_limit and errors <= error_limit)
