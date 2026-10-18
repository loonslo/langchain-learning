"""L8 安全/韧性/性能 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/resilience.py。实现下面四个函数，然后运行：

    python chapters/part8-ai-quality-optional/8.8-security-resilience-perf/gate/gate_check.py
"""

from __future__ import annotations


def call_with_retry(operation, max_attempts: int = 3, backoff_seconds: float = 0.0, sleep=None) -> dict:
    """有限重试，返回 {"result","attempts","error"}。

    max_attempts<1 或 backoff<0 -> ValueError；sleep 可注入，默认不等待；
    全部失败 result=None、attempts=max_attempts。
    """
    raise NotImplementedError("实现有限重试")


def validate_input(question: str, max_length: int = 500) -> list[str]:
    """空白、超长、含控制字符（换行/制表符除外）返回错误。"""
    raise NotImplementedError("实现输入校验")


def percentile(samples_ms: list[float], ratio: float) -> float:
    """nearest-rank 百分位；空样本或 ratio 不在 (0,1] -> ValueError。"""
    raise NotImplementedError("实现分位数")


def meets_slo(samples_ms: list[float], error_rate: float, p95_ms: float, max_error_rate: float) -> bool:
    """p95<=p95_ms 且 error_rate<=max_error_rate；空样本 -> ValueError。"""
    raise NotImplementedError("实现 SLO 判断")
