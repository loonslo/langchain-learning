"""从压测样本计算 p95、错误率和是否满足容量目标。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CapacityReport:
    p95_ms: float
    error_rate: float
    passed: bool


def report(latencies, statuses, p95_limit=2000, error_limit=0.01):
    ordered = sorted(latencies)
    index = max(0, int(len(ordered) * 0.95) - 1)
    p95 = ordered[index]
    errors = sum(x >= 500 for x in statuses) / len(statuses)
    return CapacityReport(p95, errors, p95 <= p95_limit and errors <= error_limit)
