"""L1.3 结构化输出 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
structured_output.py。实现下面两个函数，然后运行：

    python chapters/part1-foundations/1.3-structured-output/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable


class SchemaError(ValueError):
    """模型输出不符合约定结构。"""


def parse_model_json(
    text: str,
    schema: dict[str, type],
    repair_fn: Callable[[str], str] | None = None,
) -> dict:
    """解析并校验模型输出的 JSON。

    要求：
    - 接受纯 JSON、```json ... ``` 围栏、JSON 前后带说明文字；
    - 按 schema 校验必需字段和类型；int 不接受 bool；
    - 解析/校验失败时，若提供 repair_fn，只调用一次修复；
    - 修复后仍失败抛 SchemaError；
    - 成功返回原始 dict（至少包含 schema 的全部字段）。
    """
    raise NotImplementedError("实现 JSON 解析与校验")


def validate_code_review(data: dict) -> dict:
    """校验代码审查结果。

    要求：
    - data 必须是 dict；
    - summary 是非空字符串（去除首尾空白后）；
    - issues 是 list，元素都是字符串；
    - score 是 1–10 的整数（bool 不算）；
    - 返回规范化后的 {"summary","issues","score"}；
    - 任何不合法抛 SchemaError。
    """
    raise NotImplementedError("实现代码审查校验")
