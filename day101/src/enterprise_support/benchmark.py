"""推理基准的可比较统计和发布门禁。"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class RequestSample:
    latency_ms: float
    ttft_ms: float
    output_tokens: int
    success: bool


@dataclass(frozen=True)
class BenchmarkSummary:
    p50_latency_ms: float
    p95_latency_ms: float
    p95_ttft_ms: float
    output_tokens_per_second: float
    error_rate: float


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("至少需要一个样本")
    ordered = sorted(values)
    # nearest-rank：两个样本的 p95 应保留较慢的那个，不能把尾延迟平均掉。
    index = max(0, min(len(ordered) - 1, ceil(len(ordered) * percentile) - 1))
    return ordered[index]


def summarize(samples: list[RequestSample]) -> BenchmarkSummary:
    if not samples:
        raise ValueError("至少需要一个样本")
    successful = [sample for sample in samples if sample.success]
    if not successful:
        raise ValueError("没有成功请求，不能发布")
    total_generation_seconds = sum(sample.latency_ms for sample in successful) / 1000
    return BenchmarkSummary(
        p50_latency_ms=_percentile([sample.latency_ms for sample in successful], 0.5),
        p95_latency_ms=_percentile([sample.latency_ms for sample in successful], 0.95),
        p95_ttft_ms=_percentile([sample.ttft_ms for sample in successful], 0.95),
        output_tokens_per_second=sum(sample.output_tokens for sample in successful) / total_generation_seconds,
        error_rate=(len(samples) - len(successful)) / len(samples),
    )


@dataclass(frozen=True)
class InferenceSlo:
    max_p95_latency_ms: float
    max_p95_ttft_ms: float
    max_error_rate: float


def release_errors(summary: BenchmarkSummary, slo: InferenceSlo) -> tuple[str, ...]:
    errors: list[str] = []
    if summary.p95_latency_ms > slo.max_p95_latency_ms:
        errors.append("p95 总延迟超出 SLO")
    if summary.p95_ttft_ms > slo.max_p95_ttft_ms:
        errors.append("p95 TTFT 超出 SLO")
    if summary.error_rate > slo.max_error_rate:
        errors.append("错误率超出 SLO")
    return tuple(errors)
