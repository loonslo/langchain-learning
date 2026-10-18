"""L2.2 向量化与召回 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
embed_retrieve.py。实现下面三个部分，然后运行：

    python chapters/part2-rag/2.2-embed-retrieve/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable


def cosine(a: list[float], b: list[float]) -> float:
    """余弦相似度。

    要求：
    - 任一向量为空、维度不一致 -> ValueError；
    - 任一向量全 0 -> 返回 0.0；
    - 否则返回 [-1, 1] 的浮点数。
    """
    raise NotImplementedError("实现余弦相似度")


def embed_texts(
    texts: list[str],
    embed_fn: Callable[[str], list[float]],
) -> list[list[float]]:
    """逐条把文本变成向量。

    要求：
    - 空列表返回 []；
    - 文本不是 str -> ValueError；
    - embed_fn 返回空向量/非 list -> ValueError；
    - 所有向量维度必须一致，否则 ValueError。
    """
    raise NotImplementedError("实现批量向量化")


class VectorIndex:
    """内存向量索引：add 建索引，search 找 top-k。"""

    def __init__(self) -> None:
        self._rows: list[dict] = []

    def add(self, ids: list[str], vectors: list[list[float]]) -> None:
        """追加向量。

        要求：
        - ids/vectors 长度不一致、id 为空或重复、维度不一致 -> ValueError；
        - 不修改传入列表。
        """
        raise NotImplementedError("实现向量写入")

    def search(self, vector: list[float], k: int = 3) -> list[dict]:
        """返回按余弦分数降序的 [{"id": str, "score": float}]。

        要求：
        - k < 1 -> ValueError；索引为空 -> []；
        - 查询向量维度必须与索引一致，否则 ValueError；
        - 最多返回 k 条；分数相同保持写入顺序。
        """
        raise NotImplementedError("实现向量检索")
