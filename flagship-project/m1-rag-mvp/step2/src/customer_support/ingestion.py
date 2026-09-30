"""把知识目录中的 Markdown 转换成可检索、可追踪的文档块。"""

from __future__ import annotations

import hashlib
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


ZH_SEPARATORS = ["\n\n", "\n", "。", "，", " ", ""]


def load_chunks(path: Path) -> list[Document]:
    """读取一个 Markdown 文件并保留安全的来源文件名。"""

    if not path.is_file():
        raise FileNotFoundError(f"知识库文件不存在：{path}")
    documents = TextLoader(str(path), encoding="utf-8").load()
    for document in documents:
        document.metadata["source"] = path.name
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=220,
        chunk_overlap=30,
        separators=ZH_SEPARATORS,
    )
    return splitter.split_documents(documents)


def ingest_directory(directory: Path) -> list[Document]:
    """按文件名稳定排序加载 Markdown；空目录立即失败。"""

    if not directory.is_dir():
        raise FileNotFoundError(f"知识库目录不存在：{directory}")
    paths = sorted(directory.glob("*.md"))
    if not paths:
        raise ValueError(f"知识库目录没有 Markdown：{directory}")
    chunks: list[Document] = []
    for path in paths:
        for chunk in load_chunks(path):
            chunk.metadata["source_id"] = path.stem
            raw = f"{path.stem}\n{chunk.page_content}".encode("utf-8")
            chunk.metadata["chunk_id"] = hashlib.sha256(raw).hexdigest()[:12]
            chunks.append(chunk)
    return chunks
