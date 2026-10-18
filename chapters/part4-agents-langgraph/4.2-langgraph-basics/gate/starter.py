"""L4.2 LangGraph 基础 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
linear_graph.py / conditional_graph.py。实现下面两个函数，然后运行：

    python chapters/part4-agents-langgraph/4.2-langgraph-basics/gate/gate_check.py
"""

from __future__ import annotations


def build_linear():
    """最小线性图：START → step_a → step_b → END。

    要求：invoke({"history": []}) 后 history 为
    ["step_a 完成", "step_b 完成"]。
    """
    raise NotImplementedError("实现线性图")


def build_conditional():
    """带分支/循环的图：START → step_a → step_b → step_c。

    step_b 让 attempts +1；step_c 在 attempts>=2 时 approved=True 并结束，
    否则回到 step_b。要求 invoke 初始 state 后 attempts=2、approved=True，
    history 里能看到两轮校验。
    """
    raise NotImplementedError("实现分支/循环图")
