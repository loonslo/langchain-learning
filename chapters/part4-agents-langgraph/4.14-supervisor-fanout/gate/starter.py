"""L4.9 Supervisor 与并行 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
langgraph_supervisor.py。实现下面两个函数，然后运行：

    python chapters/part4-agents-langgraph/4.14-supervisor-fanout/gate/gate_check.py
"""

from __future__ import annotations

PIPELINE = ["research", "writing", "review"]


def next_stage(stage: str, pipeline: list[str] | None = None) -> str:
    """按固定流水线返回下一阶段。

    - stage 为空 -> pipeline[0]；
    - 已到最后 -> "FINISH"；
    - stage 不在 pipeline -> ValueError；
    - pipeline 为空/非 list -> ValueError。
    """
    raise NotImplementedError("实现主管推进")


def fan_in(results: list[list[str]]) -> list[str]:
    """合并并行分支结果：按输入顺序展平，去重保序；非 list -> ValueError。"""
    raise NotImplementedError("实现 fan-in 合并")
