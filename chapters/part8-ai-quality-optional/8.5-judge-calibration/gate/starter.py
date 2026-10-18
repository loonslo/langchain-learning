"""L3.4 扩展 · Judge 校准 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/judge.py。实现下面两个函数，然后运行：

    python chapters/part8-ai-quality-optional/8.5-judge-calibration/gate/gate_check.py
"""

from __future__ import annotations


def labels_at(examples: list[dict], threshold: float) -> list[tuple[int, int]]:
    """把 judge_score >= threshold 转成 1/0，返回 [(gold_label, judge_label)]。"""
    raise NotImplementedError("实现阈值标注")


def calibrate(examples: list[dict], thresholds: tuple[float, ...] = (0.5, 0.6, 0.7, 0.8)) -> dict:
    """在候选阈值中选一致率最高（并列取较小阈值）。

    返回 {"threshold","agreement","kappa","confusion"}：
    - agreement = 一致条数 / 总数；
    - confusion 是 {(gold, judge): count}，四格都要有；
    - 空样本 -> ValueError；
    - kappa = (observed - expected) / (1 - expected)；expected=1 时记 1.0。
    """
    raise NotImplementedError("实现阈值校准")
