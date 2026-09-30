import pytest

from ai_testing.risk import Risk, RiskMatrix


def test_risk_score_and_level_turn_business_impact_into_priority():
    risk = Risk("RAG-01", "retrieval", "关键政策未召回", 5, 4, "Recall@k")

    assert risk.score == 20
    assert risk.level == "critical"


def test_risk_matrix_prioritizes_high_score_and_rejects_duplicates():
    matrix = RiskMatrix()
    matrix.add(Risk("B", "api", "鉴权绕过", 5, 3, "contract test"))
    matrix.add(Risk("A", "rag", "引用错误", 4, 4, "citation test"))

    assert [item.risk_id for item in matrix.prioritized()] == ["A", "B"]
    with pytest.raises(ValueError, match="重复风险"):
        matrix.add(Risk("A", "other", "重复", 1, 1, "none"))


def test_risk_matrix_reports_missing_test_areas():
    matrix = RiskMatrix([Risk("R1", "rag", "召回", 4, 3, "recall")])

    assert matrix.uncovered_areas({"rag", "auth", "streaming"}) == {"auth", "streaming"}
