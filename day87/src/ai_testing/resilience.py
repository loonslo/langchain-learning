"""安全输入、有限重试和延迟 SLO 的离线测试工具。"""

from dataclasses import dataclass
import re
import time
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1 or self.backoff_seconds < 0:
            raise ValueError("重试次数必须大于 0，退避时间不能为负数")


def call_with_retry(
    operation: Callable[[], T],
    policy: RetryPolicy,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[T | None, int, Exception | None]:
    last_error: Exception | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return operation(), attempt, None
        except Exception as exc:  # noqa: BLE001 - 测试工具需要记录真实失败
            last_error = exc
            if attempt < policy.max_attempts:
                sleep(policy.backoff_seconds * attempt)
    return None, policy.max_attempts, last_error


def validate_input(question: str, max_length: int = 500) -> list[str]:
    errors: list[str] = []
    if not question.strip():
        errors.append("问题不能为空")
    if len(question) > max_length:
        errors.append(f"问题超过长度限制：{max_length}")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", question):
        errors.append("问题包含控制字符")
    return errors


def percentile(samples_ms: list[float], ratio: float) -> float:
    if not samples_ms or not 0 < ratio <= 1:
        raise ValueError("samples 不能为空，ratio 必须在 (0, 1] 之间")
    ordered = sorted(samples_ms)
    index = min(len(ordered) - 1, max(0, int(len(ordered) * ratio) - 1))
    return ordered[index]


def meets_slo(samples_ms: list[float], error_rate: float, p95_ms: float, max_error_rate: float) -> bool:
    return percentile(samples_ms, 0.95) <= p95_ms and error_rate <= max_error_rate
