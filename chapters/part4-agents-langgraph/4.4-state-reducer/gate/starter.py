"""L4.3 状态与 Reducer · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
state_reducer.py。实现下面四个函数，然后运行：

    python chapters/part4-agents-langgraph/4.4-state-reducer/gate/gate_check.py
"""

from __future__ import annotations


def merge_lists(old: list, new: list) -> list:
    """operator.add 的语义：返回 old+new，不修改输入。"""
    raise NotImplementedError("实现列表合并")


def keep_last_n(old: list, new: list, n: int = 4) -> list:
    """合并后只保留最近 n 条；n < 1 -> ValueError。"""
    raise NotImplementedError("实现滑动窗口 reducer")


def build_accumulate_graph():
    """两步线性图：a/b 各返回一条 log，用 operator.add 合并。

    invoke({"log": []}) 后 log 应包含两条记录。
    """
    raise NotImplementedError("实现累加图")


def build_fanout_graph():
    """三分支 fan-out 到 merge：results 用 operator.add，三条都保留。"""
    raise NotImplementedError("实现 fan-out 图")


def build_fanout_no_reducer():
    """三分支 fan-out 但 results 不写 reducer；invoke 应抛 InvalidUpdateError。"""
    raise NotImplementedError("实现无 reducer 的 fan-out 图")
