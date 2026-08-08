"""用全部知识文档创建真实向量检索器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .ingestion import ingest_directory, load_chunks

__all__ = ["build_retriever", "ingest_directory", "load_chunks"]


def build_retriever(path: Path, embeddings: Any, *, k: int, threshold: float):
    """摄取整个知识目录并创建向量检索器。"""

    from langchain_chroma import Chroma

    chunks = ingest_directory(path)
    vector_store = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name=f"day52-{uuid4().hex}",
    )
    return vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": k, "score_threshold": threshold},
    )
