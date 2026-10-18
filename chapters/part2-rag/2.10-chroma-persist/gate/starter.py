"""L2.7 向量库持久化 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
chroma_persist.py。实现下面这个类，然后运行：

    python chapters/part2-rag/2.10-chroma-persist/gate/gate_check.py
"""

from __future__ import annotations

from pathlib import Path


class StoreError(ValueError):
    """持久化/写入/查询失败。"""


class PersistentVectorStore:
    """用 JSON 文件持久化的最小向量库。"""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.rows: list[dict] = []

    def add(self, ids: list[str], vectors: list[list[float]], metadata: list[dict] | None = None) -> None:
        """追加记录。

        要求：
        - ids/vectors 长度一致；metadata 缺省为等长空 dict；
        - ID 非空且不与已有/本批重复；维度一致；
        - 不修改传入列表；
        - 不合法抛 StoreError。
        """
        raise NotImplementedError("实现写入")

    def search(self, vector: list[float], k: int = 3) -> list[dict]:
        """返回 [{"id","score","metadata"}]，按余弦分数降序。

        要求：k < 1 -> StoreError；空库 -> []；维度不一致 -> StoreError。
        """
        raise NotImplementedError("实现检索")

    def save(self) -> None:
        """把记录写到 self.path（JSON，UTF-8）。写失败 -> StoreError。"""
        raise NotImplementedError("实现保存")

    @classmethod
    def load(cls, path: str | Path) -> "PersistentVectorStore":
        """从 JSON 文件加载。

        要求：文件不存在/JSON 非法/字段缺失/ID 重复 -> StoreError。
        """
        raise NotImplementedError("实现加载")
