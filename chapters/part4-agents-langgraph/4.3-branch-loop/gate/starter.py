"""L4.3 分支与循环 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
branch_loop.py。实现下面三个函数，然后运行：

    python chapters/part4-agents-langgraph/4.3-branch-loop/gate/gate_check.py
"""

from __future__ import annotations


def improve(state: dict) -> dict:
    """quality 和 rounds 各 +1。"""
    raise NotImplementedError("实现改进节点")


def route(state: dict) -> str:
    """quality >= 5 返回 "good_enough"，否则 "keep_going"。"""
    raise NotImplementedError("实现路由")


def build_loop():
    """START → improve；quality<5 回到 improve，否则 END。"""
    raise NotImplementedError("实现循环图")
