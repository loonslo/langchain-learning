import pytest

from ai_testing.judge import JudgeExample, calibrate


def test_judge_calibration_selects_threshold_with_best_human_agreement():
    report = calibrate(
        [
            JudgeExample("a", 1, 0.91),
            JudgeExample("b", 1, 0.72),
            JudgeExample("c", 0, 0.41),
            JudgeExample("d", 0, 0.30),
        ],
        thresholds=(0.5, 0.8),
    )

    assert report.threshold == 0.5
    assert report.agreement == 1.0
    assert report.kappa == 1.0
    assert report.confusion[(1, 1)] == 2


def test_judge_requires_calibration_examples():
    with pytest.raises(ValueError, match="校准样本"):
        calibrate([])
