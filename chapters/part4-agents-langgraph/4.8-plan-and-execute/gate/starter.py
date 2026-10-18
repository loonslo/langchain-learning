"""L4.5 扩展 · 规划与执行 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
plan_and_execute.py。实现下面三个函数，然后运行：

    python chapters/part4-agents-langgraph/4.8-plan-and-execute/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable


def parse_plan(text: str, min_steps: int = 2, max_steps: int = 4) -> list[str]:
    """把模型输出的计划解析成步骤列表。

    要求：
    - 去行首编号（1. / 1) / - / •）和空白；
    - 去空行、去重、保持顺序；
    - 步数不在 [min_steps, max_steps] -> ValueError；
    - text 非字符串 -> ValueError。
    """
    raise NotImplementedError("实现计划解析")


def run_plan(
    task: str,
    plan_fn: Callable[[str], list[str]],
    execute_fn: Callable[[str, str], str],
    max_steps: int = 10,
) -> dict:
    """先规划再逐步执行。

    返回 {"task","plan","results","error"}。
    要求：
    - 空任务 -> ValueError；max_steps < 1 -> ValueError；
    - plan_fn/execute_fn 异常 -> error 可读，不崩；
    - 计划超过 max_steps -> 只执行前 max_steps 步，error="plan_too_long"；
    - 正常 -> results 与 plan 等长。
    """
    raise NotImplementedError("实现规划执行")
