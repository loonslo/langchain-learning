"""L4.1 Agent 模式 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
agent_patterns.py。实现下面四个函数，然后运行：

    python chapters/part4-agents-langgraph/4.1-agent-patterns/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable


def fixed_workflow(a: int, b: int) -> int:
    """固定工作流：校验整数后返回 a+b；bool/非整数 -> ValueError。"""
    raise NotImplementedError("实现固定工作流")


def scripted_planner(state: dict) -> dict:
    """脚本决策器：没有 observations 就返回 add，否则 finish。"""
    raise NotImplementedError("实现脚本决策器")


def initial_state() -> dict:
    """返回含 question/steps/observations/decision/status/error 的初始 state。"""
    raise NotImplementedError("实现初始状态")


def build_graph(
    planner: Callable[[dict], dict] | None = None,
    *,
    max_steps: int = 2,
):
    """用 LangGraph 搭“决策 → 工具 → 决策”的有界循环。

    要求：
    - planner 缺省用 scripted_planner；max_steps < 1 -> ValueError；
    - 只允许 add；未知工具 -> status=failed、error=白名单；
    - 预算耗尽 -> status=failed、error=预算；
    - planner 抛 ValueError/TimeoutError -> status=failed；
    - 参数错误 -> tool 节点记 failed，不伪装成功；
    - 正常路径 -> status=done，observations 含结果。
    """
    raise NotImplementedError("实现有界循环图")
