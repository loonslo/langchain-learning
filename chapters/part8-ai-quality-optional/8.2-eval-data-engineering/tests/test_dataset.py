import json

import pytest

from ai_testing.dataset import EvalCase, EvalDataset


def test_dataset_validates_cases_and_supports_tag_slices():
    dataset = EvalDataset(
        [
            EvalCase("refund", "退款多久到账？", ("3–5",), ("refund.md",), ("rag",)),
            EvalCase("unknown", "你们支持海外股票吗？", tags=("refusal",), should_refuse=True),
        ],
        version="2026.08",
    )

    assert dataset.validate() == {}
    assert [case.case_id for case in dataset.by_tag("refusal")] == ["unknown"]


def test_dataset_round_trip_preserves_version_and_tuple_fields(tmp_path):
    path = tmp_path / "eval.json"
    source = EvalDataset([EvalCase("x", "问题", ("答案",), tags=("smoke",))], "v2")

    source.save(path)
    loaded = EvalDataset.load(path)

    assert loaded.version == "v2"
    assert loaded.by_tag("smoke")[0].expected_keywords == ("答案",)
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == "v2"


def test_invalid_non_refusal_case_is_reported_and_duplicate_ids_fail():
    dataset = EvalDataset([EvalCase("missing-answer", "问题")])

    assert "missing-answer" in dataset.validate()
    with pytest.raises(ValueError, match="重复 case_id"):
        dataset.add(EvalCase("missing-answer", "另一个问题", ("x",)))
