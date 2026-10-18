"""L2.8 重排与多模态 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
multimodal_rerank.py。实现下面两个函数，然后运行：

    python chapters/part2-rag/2.11-multimodal-rerank/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable


def rerank(
    query: str,
    docs: list[dict],
    score_fn: Callable[[str, str], float],
    top_k: int = 3,
) -> list[dict]:
    """按 score_fn 对候选重排。

    docs 形如 [{"id": str, "text": str}, ...]。
    返回 [{"id","text","score"}]，按分数降序，最多 top_k 条。
    要求：
    - top_k < 1 -> ValueError；
    - docs 为空 -> []；
    - 片段缺 id/text 或类型错 -> ValueError；
    - score_fn 返回非数值或抛异常 -> ValueError；
    - 同分保持原顺序（稳定排序）；
    - 不修改输入。
    """
    raise NotImplementedError("实现重排")


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    """计算 recall@k：前 k 个结果覆盖了多少相关 ID。

    要求：
    - k < 1 -> ValueError；
    - 没有相关 ID -> 返回 0.0；
    - 返回 [0,1] 的浮点数。
    """
    raise NotImplementedError("实现 recall@k")
