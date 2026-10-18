"""L3.5 Ragas 与指标口径 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
dataset_ragas.py。实现下面三个函数，然后运行：

    python chapters/part3-evals/3.5-eval-dataset-ragas/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable

TYPES = {"fact", "multi_hop", "refuse", "citation"}


def merge_sets(base: list[dict], extra: list[dict]) -> list[dict]:
    """合并基础集与补充集。

    要求：
    - 不修改输入；
    - 合并后 ID 唯一，重复 -> ValueError；
    - 每行必须含 id/type；缺字段 -> ValueError；
    - 保持 base 在前、extra 在后的顺序。
    """
    raise NotImplementedError("实现评测集合并")


def validate_full_set(rows: list[dict]) -> dict:
    """校验合并后的评测集。

    返回 {"ok": bool, "errors": list[str], "type_counts": dict, "refuse_count": int}。
    要求：
    - 空集 -> ok=False，含 empty；
    - type 必须合法；id 唯一；拒答题 must_refuse=True；
    - 拒答题的 keywords 应为空（拒答不靠关键词判分）。
    """
    raise NotImplementedError("实现全集校验")


def build_ragas_rows(
    cases: list[dict],
    ask_fn: Callable[[dict], dict],
) -> dict:
    """把非拒答样本跑成 RAGAS 需要的四列。

    ask_fn(case) 返回 {"answer": str, "contexts": list[str]}。
    返回 {"question": [...], "answer": [...], "contexts": [...], "ground_truth": [...]}。
    要求：
    - 跳过 type="refuse"；
    - 缺 answer/contexts、类型错 -> ValueError；
    - 不修改 cases。
    """
    raise NotImplementedError("实现 RAGAS 行构造")
