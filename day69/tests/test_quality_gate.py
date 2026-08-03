from customer_support.quality_gate import check


def test_low_or_missing_metric_closes_gate():
    assert check({"pass_rate": 1, "citation_rate": 0.8}) == [
        "citation_rate 低于阈值",
        "缺少 refusal_rate",
    ]
