"""摄取全部知识，并创建真正接入问答链的混合检索器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .ingestion import ingest_directory, load_chunks
from .retrieval import HybridRetriever, KeywordRetriever

__all__ = ["build_retriever", "ingest_directory", "load_chunks"]


def build_retriever(path: Path, embeddings: Any, *, k: int, threshold: float):
    """用同一批文档创建语义、关键词两路检索并通过 RRF 融合。"""

    from langchain_chroma import Chroma

    chunks = ingest_directory(path)
    vector_store = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name=f"day54-{uuid4().hex}",
    )
    semantic = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": k, "score_threshold": threshold},
    )
    keyword = KeywordRetriever(chunks, k=k)
    return HybridRetriever(semantic, keyword, limit=k)
