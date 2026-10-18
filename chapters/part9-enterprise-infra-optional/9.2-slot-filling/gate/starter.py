"""L5.9 槽位填充 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/slots.py。实现下面三个函数，然后运行：

    python chapters/part9-enterprise-infra-optional/9.2-slot-filling/gate/gate_check.py
"""

from __future__ import annotations

REQUIRED = {
    "refund_status": ("order_id",),
    "order_status": ("order_id",),
    "shipping": (),
    "human_handoff": (),
    "unknown": (),
}


def extract_slots(question: str) -> dict[str, str]:
    """提取订单号：支持“订单号/订单 id/order id”，值转大写；没有返回 {}。"""
    raise NotImplementedError("实现槽位提取")


def resolve_slots(intent: str, question: str, previous: dict[str, str] | None = None) -> dict:
    """合并上一轮槽位 + 本轮提取（新值覆盖），返回 {"intent","values","missing"}。

    - intent 不在 REQUIRED -> ValueError；
    - missing 按 REQUIRED[intent] 顺序列出空值；
    - 不修改 previous。
    """
    raise NotImplementedError("实现槽位合并")


def next_question(state: dict) -> str | None:
    """有缺失返回订单号追问，否则 None。"""
    raise NotImplementedError("实现追问")
