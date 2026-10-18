"""L1.3 扩展 · 稳定 JSON 契约 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/structured_json.py。实现 parse_model_json，然后运行：

    python chapters/part9-enterprise-infra-optional/9.3-stable-json-output/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable


class StructuredOutputError(ValueError):
    pass


def parse_model_json(
    text: str,
    fields: dict[str, type],
    *,
    allow_extra: bool = False,
    repair: Callable[[str], str] | None = None,
) -> dict:
    """把模型文本收敛成严格 JSON 对象。

    要求：
    - 支持 ```json 围栏；
    - 必须是 JSON 对象；非 JSON/数组 -> StructuredOutputError；
    - 字段齐全；类型严格（bool 不能当 int）；
    - 多余字段在 allow_extra=False 时报错；
    - 首次失败才调用一次 repair；仍失败抛错；
    - 返回值只含声明字段。
    """
    raise NotImplementedError("实现 JSON 契约")
