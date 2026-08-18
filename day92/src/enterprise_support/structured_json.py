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
    """最多尝试原输出和一次修复，绝不形成无边界模型循环。"""
    attempts = [text]
    if repair is not None:
        attempts.append(repair(text))
    errors: list[str] = []
    for candidate in attempts:
        try:
            return validate_json(_object_from_text(candidate), schema)
        except StructuredOutputError as exc:
            errors.append(str(exc))
    raise StructuredOutputError("；".join(errors))
