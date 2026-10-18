"""L4.10 流式与人工介入 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
streaming_hitl.py。实现下面两个函数，然后运行：

    python chapters/part4-agents-langgraph/4.11-streaming-hitl/gate/gate_check.py
"""

from __future__ import annotations

DANGEROUS = {"delete", "send_email", "pay"}


def needs_approval(action: str, amount: float | None = None, threshold: float = 1000) -> bool:
    """是否需要人工审批。

    规则：
    - action 在 DANGEROUS 中 -> True；
    - amount 非 None 且 > threshold -> True；
    - 其他 -> False；
    - action 非空字符串；amount < 0 -> ValueError。
    """
    raise NotImplementedError("实现审批判断")


def resolve_approval(decision: str) -> str:
    """把人工输入归一化：yes -> "approved"，no -> "cancelled"，其他 -> ValueError。"""
    raise NotImplementedError("实现审批结果")
