"""推理基准的可比较统计和发布门禁。"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class RequestSample:
    """一次请求的结果：总延迟、首字延迟（TTFT）、输出 token 数、是否成功。"""

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
    """汇总成功请求的延迟分位数和吞吐；错误率按全部样本计算。

    输出吞吐 = 成功请求的输出 token 总数 ÷ 成功请求的延迟总和，相当于把请求串行执行，
    并发压测时会低估真实吞吐，应另用墙钟时间计算。没有样本或没有成功请求时抛 ValueError。
    """
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
    """发布门槛：p95 总延迟、p95 首字延迟和错误率的上限。"""

    max_p95_latency_ms: float
    max_p95_ttft_ms: float
    max_error_rate: float


def release_errors(summary: BenchmarkSummary, slo: InferenceSlo) -> tuple[str, ...]:
    """返回超出 SLO 的项（空元组表示可发布）；只看性能，质量回归要另外通过。"""
    errors: list[str] = []
    if summary.p95_latency_ms > slo.max_p95_latency_ms:
        errors.append("p95 总延迟超出 SLO")
    if summary.p95_ttft_ms > slo.max_p95_ttft_ms:
        errors.append("p95 TTFT 超出 SLO")
    if summary.error_rate > slo.max_error_rate:
        errors.append("错误率超出 SLO")
    return tuple(errors)
