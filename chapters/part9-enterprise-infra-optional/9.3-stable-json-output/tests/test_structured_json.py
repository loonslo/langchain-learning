import pytest

from src.enterprise_support.structured_json import (
    JsonSchema,
    StructuredOutputError,
    parse_model_json,
)


SCHEMA = JsonSchema({"answer": str, "handoff": bool})


def test_accepts_exact_or_fenced_json_only():
    assert parse_model_json('```json\n{"answer":"已登记","handoff":false}\n```', SCHEMA) == {
        "answer": "已登记",
        "handoff": False,
    }


def test_repair_is_single_and_result_is_validated_again():
    calls = []

    def repair(_: str) -> str:
        calls.append("repair")
        return '{"answer":"请提供订单号","handoff":false}'

    result = parse_model_json("抱歉，结果如下：{}", SCHEMA, repair=repair)
    assert result["answer"] == "请提供订单号"
    assert calls == ["repair"]


def test_rejects_prose_extra_fields_and_repair_exhaustion():
    with pytest.raises(StructuredOutputError):
        parse_model_json('{"answer":"x","handoff":false,"debug":true}', SCHEMA)
    with pytest.raises(StructuredOutputError):
        parse_model_json("not json", SCHEMA, repair=lambda _: "still not json")


def test_valid_output_never_calls_repair():
    def repair(_: str) -> str:
        raise AssertionError("合法输出不应触发修复调用")

    assert parse_model_json('{"answer":"ok","handoff":false}', SCHEMA, repair=repair)["answer"] == "ok"
