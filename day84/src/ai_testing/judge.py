"""LLM-as-judge 的离线校准：先和人工标签比较，再决定是否采信分数。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class JudgeExample:
    case_id: str
    gold_label: int
    judge_score: float


@dataclass(frozen=True)
class CalibrationReport:
    threshold: float
    agreement: float
    kappa: float
    confusion: dict[tuple[int, int], int]


def labels_at(examples: list[JudgeExample], threshold: float) -> list[tuple[int, int]]:
    return [
        (example.gold_label, int(example.judge_score >= threshold))
        for example in examples
    ]


def _kappa(pairs: list[tuple[int, int]]) -> float:
    if not pairs:
        return 0.0
    observed = sum(gold == judged for gold, judged in pairs) / len(pairs)
    gold_positive = sum(gold for gold, _ in pairs) / len(pairs)
    judged_positive = sum(judged for _, judged in pairs) / len(pairs)
    expected = gold_positive * judged_positive + (1 - gold_positive) * (1 - judged_positive)
    return 1.0 if expected == 1.0 else (observed - expected) / (1 - expected)


def calibrate(examples: list[JudgeExample], thresholds: tuple[float, ...] = (0.5, 0.6, 0.7, 0.8)) -> CalibrationReport:
    if not examples:
        raise ValueError("至少需要一个校准样本")
    candidates = []
    for threshold in thresholds:
        pairs = labels_at(examples, threshold)
        agreement = sum(gold == judged for gold, judged in pairs) / len(pairs)
        candidates.append((agreement, threshold, pairs))
    agreement, threshold, pairs = max(candidates, key=lambda item: (item[0], -item[1]))
    confusion = {(gold, judged): pairs.count((gold, judged)) for gold in (0, 1) for judged in (0, 1)}
    return CalibrationReport(threshold, agreement, _kappa(pairs), confusion)
