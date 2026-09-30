"""把模型文本收敛为可审计的 JSON 契约。"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


_FENCED_JSON = re.compile(r"^\s*```(?:json)?\s*(\{.*\})\s*```\s*$", re.DOTALL | re.I)


@dataclass(frozen=True)
class JsonSchema:
    """字段名 → 期望类型；allow_extra=False 时不允许多余字段。类型比较是严格的，bool 不能当 int。"""

    fields: Mapping[str, type]
    allow_extra: bool = False


class StructuredOutputError(ValueError):
    pass


def _object_from_text(text: str) -> dict[str, Any]:
    candidate = text.strip()
    fenced = _FENCED_JSON.fullmatch(candidate)
    if fenced:
        candidate = fenced.group(1)
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError("模型输出不是完整 JSON 对象") from exc
    if not isinstance(value, dict):
        raise StructuredOutputError("模型输出必须是 JSON 对象")
    return value


def validate_json(value: dict[str, Any], schema: JsonSchema) -> dict[str, Any]:
    """校验字段齐全、类型严格一致、没有多余字段（除非允许）；返回值只含 schema 声明的字段。"""
    missing = set(schema.fields) - set(value)
    extras = set(value) - set(schema.fields)
    if missing:
        raise StructuredOutputError(f"缺少字段：{sorted(missing)}")
    if extras and not schema.allow_extra:
        raise StructuredOutputError(f"不允许额外字段：{sorted(extras)}")
    for name, expected_type in schema.fields.items():
        # bool 是 int 的子类，业务 JSON 里必须严格区分。
        if type(value[name]) is not expected_type:
            raise StructuredOutputError(f"字段 {name} 必须是 {expected_type.__name__}")
    return {name: value[name] for name in schema.fields}


def parse_model_json(
    text: str,
    schema: JsonSchema,
    *,
    repair: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """校验原输出；失败后才调用一次 repair 再校验，仍失败就抛错，不会形成无边界的模型循环。"""
    errors: list[str] = []
    try:
        return validate_json(_object_from_text(text), schema)
    except StructuredOutputError as exc:
        errors.append(str(exc))
    if repair is not None:
        try:
            return validate_json(_object_from_text(repair(text)), schema)
        except StructuredOutputError as exc:
            errors.append(str(exc))
    raise StructuredOutputError("；".join(errors))
