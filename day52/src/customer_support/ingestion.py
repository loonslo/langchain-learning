"""多文档摄取：保留来源，并为每个切块生成可重复的业务 ID。"""

from __future__ import annotations
import hashlib
from pathlib import Path
from langchain_core.documents import Document
from customer_support.knowledge import load_chunks


def ingest_directory(directory: Path) -> list[Document]:
    """按文件名稳定排序加载 Markdown；空目录立即失败。"""
    paths = sorted(directory.glob("*.md"))
    if not paths:
        raise ValueError(f"知识库目录没有 Markdown：{directory}")
    chunks: list[Document] = []
    for path in paths:
        for chunk in load_chunks(path):
            chunk.metadata["source_id"] = path.stem
            raw = f"{path.stem}\n{chunk.page_content}".encode()
            chunk.metadata["chunk_id"] = hashlib.sha256(raw).hexdigest()[:12]
            chunks.append(chunk)
    return chunks
