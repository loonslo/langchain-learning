"""安全输入、有限重试和延迟 SLO 的离线测试工具。"""

from dataclasses import dataclass
from math import ceil
import re
import time
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """有限重试：最多 max_attempts 次（含第一次），第 n 次失败后等待 backoff_seconds × n 秒（线性退避）。"""

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
    """执行 operation，失败后按策略重试，返回 (结果, 实际尝试次数, 最后一次异常)。

    成功时异常为 None；全部失败时结果为 None，尝试次数等于 max_attempts。
    这里对所有 Exception 都重试；真实系统只该重试超时、限流等临时错误，参数错误和鉴权失败应立即失败。
    sleep 可注入，测试时传入空函数就不会真的等待。
    """
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
    """返回输入问题的错误列表：空白、超长、含控制字符（换行和制表符除外）。不检测提示注入。"""
    errors: list[str] = []
    if not question.strip():
        errors.append("问题不能为空")
    if len(question) > max_length:
        errors.append(f"问题超过长度限制：{max_length}")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", question):
        errors.append("问题包含控制字符")
    return errors


def percentile(samples_ms: list[float], ratio: float) -> float:
    """nearest-rank 百分位：取升序后第 ceil(n × ratio) 个样本，不做插值。
    小样本也保留最慢的请求：10 个样本的 p95 是最大值，而不是第 9 个。ratio 取值范围 (0, 1]。
    """
    if not samples_ms or not 0 < ratio <= 1:
        raise ValueError("samples 不能为空，ratio 必须在 (0, 1] 之间")
    ordered = sorted(samples_ms)
    index = min(len(ordered) - 1, max(0, ceil(len(ordered) * ratio) - 1))
    return ordered[index]


def meets_slo(samples_ms: list[float], error_rate: float, p95_ms: float, max_error_rate: float) -> bool:
    """p95 不超过 p95_ms 且错误率不超过 max_error_rate 才返回 True；样本为空抛 ValueError，不会默认通过。"""
    return percentile(samples_ms, 0.95) <= p95_ms and error_rate <= max_error_rate
