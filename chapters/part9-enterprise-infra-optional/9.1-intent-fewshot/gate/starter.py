"""L9 意图 few-shot · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/intent.py。实现下面两个函数，然后运行：

    python chapters/part9-enterprise-infra-optional/9.1-intent-fewshot/gate/gate_check.py
"""

from __future__ import annotations

INTENTS = {"refund_status", "order_status", "shipping", "human_handoff", "unknown"}


def build_intent_prompt(question: str) -> str:
    """把问题填入 few-shot 提示词；空问题 -> ValueError。

    提示词必须包含：五个意图名、JSON 契约、至少 3 个示例、用户问题。
    """
    raise NotImplementedError("实现提示词")


def parse_intent_payload(payload: str | dict) -> dict:
    """校验模型 JSON，返回 {"intent","confidence"}。

    - 非对象/坏 JSON -> ValueError；
    - intent 不在 INTENTS -> ValueError；
    - confidence 缺失/非数值/不在 [0,1] -> ValueError。
    """
    raise NotImplementedError("实现意图解析")
