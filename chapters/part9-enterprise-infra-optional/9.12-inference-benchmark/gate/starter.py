"""L5.8 扩展 · 推理基准 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/benchmark.py。实现下面三个函数，然后运行：

    python chapters/part9-enterprise-infra-optional/9.12-inference-benchmark/gate/gate_check.py
"""

from __future__ import annotations


def percentile(values: list[float], p: float) -> float:
    """nearest-rank 分位数；空列表 -> ValueError；p 不在 0-1 -> ValueError。"""
    raise NotImplementedError("实现分位数")


def summarize(samples: list[dict]) -> dict:
    """只统计成功样本的延迟/TTFT 分位数和吞吐；错误率按全部样本。

    samples 每项 {"latency_ms","ttft_ms","output_tokens","success"}。
    返回 p50_latency_ms/p95_latency_ms/p95_ttft_ms/output_tokens_per_second/error_rate。
    空样本或无成功样本 -> ValueError。
    """
    raise NotImplementedError("实现基准汇总")


def release_errors(summary: dict, slo: dict) -> tuple[str, ...]:
    """p95 延迟、p95 TTFT、错误率超限时返回对应错误；否则空元组。"""
    raise NotImplementedError("实现发布门禁")
