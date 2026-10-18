"""L2.5 混合检索 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
hybrid_search.py。实现下面两个函数，然后运行：

    python chapters/part2-rag/2.8-hybrid-search/gate/gate_check.py
"""

from __future__ import annotations


def rrf_fuse(
    rankings: list[list[str]],
    k: int = 60,
    weights: list[float] | None = None,
) -> list[dict]:
    """Reciprocal Rank Fusion（RRF）。

    输入多路排序（每路是 id 列表，rank 从 1 开始）。
    返回 [{"id": str, "score": float}]，按 score 降序。
    要求：
    - 空 rankings -> []；
    - k < 1 -> ValueError；
    - weights 缺省为全 1；长度与 rankings 不一致、负数 -> ValueError；
    - 同一路里重复的 id 只按第一次出现计分；
    - 同分按首次出现顺序稳定排列。
    """
    raise NotImplementedError("实现 RRF 融合")


def hybrid_search(
    vector_ids: list[str],
    bm25_ids: list[str],
    k: int = 4,
    weights: tuple[float, float] = (0.5, 0.5),
) -> list[dict]:
    """把向量和 BM25 两路结果融合，取 top-k。

    要求：
    - k < 1 -> ValueError；
    - 两路都为空 -> []；
    - 其余情况调用 rrf_fuse([vector_ids, bm25_ids], weights=[...]) 并截断。
    """
    raise NotImplementedError("实现混合检索")
