from ai_testing.ci_gate import LayerResult, evaluate_gate, flaky_tests


def test_gate_fails_when_required_layer_or_flaky_test_exists():
    report = evaluate_gate(
        [LayerResult("unit", True), LayerResult("rag-eval", False, "recall too low")],
        {"test_stable": [True, True], "test_flaky": [True, False]},
    )

    assert report.passed is False
    assert report.failed_layers == ("rag-eval",)
    assert report.flaky_tests == ("test_flaky",)


def test_optional_layer_does_not_block_but_flaky_detection_is_explicit():
    report = evaluate_gate([LayerResult("load", False, required=False)])

    assert report.passed is True
    assert flaky_tests({"a": [True, False], "b": [False, False]}) == ("a",)
