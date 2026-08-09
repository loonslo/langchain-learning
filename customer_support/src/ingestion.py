"""把知识目录中的 Markdown 转换成可检索、可追踪的文档块。

一篇长文不能总是整体送去检索，因此会先按中文语境切成较小的 ``Document``。
每个文档块保留来源与稳定编号，后续回答才能展示“这句话来自哪份资料”。
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 切分器会按此顺序尝试断开文本：先在段落边界切，实在不行才按更细的标点或字符切。
# 最后的空字符串保证超长文本无论如何都能被分块。
ZH_SEPARATORS = ["\n\n", "\n", "。", "，", " ", ""]


def load_chunks(path: Path) -> list[Document]:
    """读取一个 Markdown 文件并切成文档块，保留安全的来源文件名。"""

    if not path.is_file():
        raise FileNotFoundError(f"知识库文件不存在：{path}")
    # TextLoader 返回 LangChain 的 Document 列表；即使这里只读一个文件，接口仍是列表。
    documents = TextLoader(str(path), encoding="utf-8").load()
    for document in documents:
        document.metadata["source"] = path.name
    # ``chunk_overlap`` 让相邻块共享少量文字，避免一句话恰好在边界处被拆断。
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=220,
        chunk_overlap=30,
        separators=ZH_SEPARATORS,
    )
    return splitter.split_documents(documents)


def ingest_directory(directory: Path) -> list[Document]:
    """按文件名稳定排序加载目录中的 Markdown；空目录立即失败。

    稳定排序的好处是同样的资料每次得到同样的处理顺序，便于测试和排查问题。
    """

    if not directory.is_dir():
        raise FileNotFoundError(f"知识库目录不存在：{directory}")
    paths = sorted(directory.glob("*.md"))
    if not paths:
        raise ValueError(f"知识库目录没有 Markdown：{directory}")
    chunks: list[Document] = []
    for path in paths:
        for chunk in load_chunks(path):
            # source_id 用“文件名（不带扩展名）”表示资料来源的业务标识。
            chunk.metadata["source_id"] = path.stem
            # 内容相同的块会得到相同的 SHA-256 截断编号，便于跨次运行追踪和去重。
            raw = f"{path.stem}\n{chunk.page_content}".encode("utf-8")
            chunk.metadata["chunk_id"] = hashlib.sha256(raw).hexdigest()[:12]
            chunks.append(chunk)
    return chunks
