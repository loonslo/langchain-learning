"""L3.2 扩展 · 反馈闭环 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/feedback_loop.py。实现 FeedbackQueue，然后运行：

    python chapters/part8-ai-quality-optional/8.10-production-feedback-loop/gate/gate_check.py
"""

from __future__ import annotations

from pathlib import Path


class FeedbackQueue:
    def submit(self, item: dict) -> bool:
        """入队；rating 只能 -1/1，case_id/question 非空；重复 id 返回 False。"""
        raise NotImplementedError("实现入队")

    def review_queue(self) -> list[dict]:
        """只返回 rating<0 且 status=pending 的项。"""
        raise NotImplementedError("实现审核队列")

    def approve(self, case_id: str) -> dict:
        """标记 approved；不存在 -> KeyError。"""
        raise NotImplementedError("实现审核通过")

    def export_regression_cases(self, path: Path) -> int:
        """把 approved 项写成 JSON（id/question/answer/sources/reason），返回数量。"""
        raise NotImplementedError("实现导出")
