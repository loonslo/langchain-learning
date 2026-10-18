"""L8 契约与不变量 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/contracts.py。实现下面两个函数，然后运行：

    python chapters/part8-ai-quality-optional/8.3-mock-contract-invariant/gate/gate_check.py
"""

from __future__ import annotations


def validate_chat_response(payload: dict) -> list[str]:
    """返回全部契约错误（不抛异常）。

    - answer 非空字符串；
    - sources 是字符串列表；
    - ticket_id 若存在且非 None，必须是字符串。
    """
    raise NotImplementedError("实现契约校验")


def assert_invariants(payload: dict) -> None:
    """契约通过后检查业务不变量，违反抛 AssertionError：

    - 答案含“没有足够信息”时不能带 sources；
    - 有 ticket_id 且无 sources 时，答案必须包含“人工”。
    """
    raise NotImplementedError("实现不变量检查")
