"""L8 评测数据工程 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/dataset.py。实现 EvalCase/EvalDataset，然后运行：

    python chapters/part8-ai-quality-optional/8.2-eval-data-engineering/gate/gate_check.py
"""

from __future__ import annotations

from pathlib import Path


def validate_case(case: dict) -> list[str]:
    """case_id/question 非空；非拒答至少一个 expected_keywords。"""
    raise NotImplementedError("实现用例校验")


class EvalDataset:
    def __init__(self, cases: list[dict] | None = None, version: str = "v1"):
        raise NotImplementedError("初始化数据集")

    def add(self, case: dict) -> None:
        """重复 case_id -> ValueError。"""
        raise NotImplementedError("实现添加")

    def validate(self) -> dict:
        """返回 {case_id: errors}，只含有问题的用例。"""
        raise NotImplementedError("实现整体校验")

    def by_tag(self, tag: str) -> list[dict]:
        """按加入顺序返回带标签的用例。"""
        raise NotImplementedError("实现标签筛选")

    def save(self, path: Path) -> None:
        """写 {"version","cases"} JSON。"""
        raise NotImplementedError("实现保存")

    @classmethod
    def load(cls, path: Path) -> "EvalDataset":
        """读取 save 输出；缺省字段用默认值。"""
        raise NotImplementedError("实现加载")
