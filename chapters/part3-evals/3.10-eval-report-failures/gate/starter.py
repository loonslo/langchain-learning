"""L3.6 扩展 · 失败诊断 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
failure_diagnosis.py。实现下面三个函数，然后运行：

    python chapters/part3-evals/3.10-eval-report-failures/gate/gate_check.py
"""

from __future__ import annotations

from pathlib import Path


def load_failures(path: str | Path) -> tuple[list[dict], str]:
    """读取失败库，返回 (失败列表, 模式)。

    要求：
    - 文件不存在/JSON 非法 -> ValueError；
    - 只保留 passed=False（缺省视为通过，过滤掉）；
    - 任一失败含非空 retrieval_context -> "live"，否则 "offline"。
    """
    raise NotImplementedError("实现失败库加载")


def classify_by_hard_metrics(failure: dict) -> tuple[str, str]:
    """按硬指标做弱信号分组。

    顺序：
    1. refusal_ok=False -> ("拒答逻辑层(疑似)", 原因)；
    2. citation_score < 0.67 -> ("检索/引用层(疑似)", 原因)；
    3. keyword_score < 0.67 -> ("生成层(疑似)", 原因)；
    4. 否则 -> ("其他/未覆盖(疑似)", 原因)。
    """
    raise NotImplementedError("实现失败分组")


def summarize_layers(results: list[dict]) -> dict:
    """统计各 layer_suspected 的数量，返回 {layer: count}。"""
    raise NotImplementedError("实现分层统计")
