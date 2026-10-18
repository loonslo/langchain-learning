"""L3.2 评测集建设 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
dataset_build.py。实现下面两个函数，然后运行：

    python chapters/part3-evals/3.4-eval-dataset-build/gate/gate_check.py
"""

from __future__ import annotations

SCHEMA_FIELDS = ["id", "question", "reference", "keywords", "expect_source", "type", "should_refuse"]
TYPES = {"fact", "multi_hop", "refuse", "citation"}


def validate_dataset(rows: list[dict]) -> dict:
    """校验评测集 schema。

    返回：
    - ok: bool
    - errors: list[str]（每条都带 id 或行号）
    - type_counts: dict[str,int]

    规则：
    - 空列表 -> ok=False，errors 含 "empty"；
    - 每行必须是 dict，且含 SCHEMA_FIELDS 全部字段；
    - id 非空且唯一；question/reference 非空字符串；
    - keywords 必须是 list；should_refuse 必须是 bool；
    - type 必须在 TYPES 内；
    - 逐条收集错误，不因第一条错误中断。
    """
    raise NotImplementedError("实现评测集校验")


def coverage(rows: list[dict]) -> dict:
    """返回 {"total","types","missing_types"}。

    types 只统计 TYPES 内的类型；missing_types 是 TYPES - 已出现类型。
    """
    raise NotImplementedError("实现题型覆盖")
