"""L4.6 可观测性 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
observability.py。实现下面两个函数，然后运行：

    python chapters/part4-agents-langgraph/4.9-observability/gate/gate_check.py
"""

from __future__ import annotations


def make_trace_record(node: str, update: dict, ts: float) -> dict:
    """生成一行结构化轨迹。

    返回 {"ts","node","update_keys","preview"}：
    - update_keys 是 update 的键列表；
    - preview 把每个值转成字符串并截断到 40 字符；
    - node 非空、ts>=0、update 是 dict，否则 ValueError。
    """
    raise NotImplementedError("实现轨迹记录")


def summarize_trace(records: list[dict]) -> dict:
    """汇总轨迹。

    返回 {"total","nodes","slowest","errors"}：
    - nodes 是 {node: 次数}；
    - slowest 是 ts 最大的 node（空 -> None）；
    - errors 是含 error 字段非空的记录列表；
    - 空列表 -> total=0、nodes={}、slowest=None、errors=[]。
    """
    raise NotImplementedError("实现轨迹汇总")
