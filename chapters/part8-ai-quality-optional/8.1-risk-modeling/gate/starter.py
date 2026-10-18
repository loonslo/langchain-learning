"""L8 风险建模 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/risk.py。实现 RiskMatrix，然后运行：

    python chapters/part8-ai-quality-optional/8.1-risk-modeling/gate/gate_check.py
"""

from __future__ import annotations


class RiskMatrix:
    def add(self, risk: dict) -> None:
        """risk: risk_id/area/scenario/impact/likelihood/control。

        - risk_id/area 非空；impact/likelihood 1–5；否则 ValueError；
        - risk_id 重复 -> ValueError。
        """
        raise NotImplementedError("实现风险入表")

    def prioritized(self) -> list[dict]:
        """按 score=impact*likelihood 降序，同分按 risk_id 升序。"""
        raise NotImplementedError("实现风险排序")

    def uncovered_areas(self, required: set[str]) -> set[str]:
        """返回 required 中没有风险条目的领域。"""
        raise NotImplementedError("实现覆盖检查")


def risk_level(impact: int, likelihood: int) -> str:
    """score>=16 critical，>=9 high，>=4 medium，否则 low；越界 -> ValueError。"""
    raise NotImplementedError("实现风险分级")
