"""把 Markdown 客服资料转换成可以按语义搜索的 Retriever。

数据流：Path → TextLoader → Document → TextSplitter → chunks → Chroma → Retriever。

这个模块只负责“准备和查找资料”，不负责组织自然语言答案。生成答案的工作位于
``assistant.py``，这样检索失败和生成失败可以分别测试、分别改进。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# RecursiveCharacterTextSplitter 会从左到右尝试这些边界。
# 优先按段落/句子切分，最后的空字符串表示实在无法切分时才逐字符兜底。
ZH_SEPARATORS = ["\n\n", "\n", "。", "，", " ", ""]


def load_chunks(path: Path) -> list[Document]:
    """读取一份 Markdown，并返回适合检索的小块 Document。

    Args:
        path: 知识库 Markdown 的完整路径。

    Returns:
        切分后的 LangChain ``Document`` 列表。每个 Document 都保留 ``source``，
        后面生成引用时只相信这个 metadata，不相信 LLM 自己声称的来源。

    Raises:
        FileNotFoundError: 配置指向了不存在的资料时立即失败，而不是创建空知识库。
    """

    # 1. 在加载模型之前检查输入文件，配置错误可以更快暴露。
    if not path.exists():
        raise FileNotFoundError(f"知识库文件不存在：{path}")

    # 2. TextLoader 把一个 Markdown 文件包装成 LangChain Document 列表。
    # 此时 document.page_content 是正文，document.metadata 保存来源等附加信息。
    documents = TextLoader(str(path), encoding="utf-8").load()

    # 3. 统一使用文件名作为对外来源，避免向用户泄露本机绝对路径。
    for document in documents:
        document.metadata["source"] = path.name

    # 4. 文档太长时，整篇 embedding 会让不同主题互相干扰，因此先切成小块。
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=220,
        chunk_overlap=30,
        separators=ZH_SEPARATORS,
    )
    return splitter.split_documents(documents)


def build_retriever(path: Path, embeddings: Any, *, k: int, threshold: float):
    """把文档块写入内存 Chroma，并返回统一 Retriever 接口。

    ``embeddings`` 通过参数传入，而不是在这里创建，测试或后续更换模型时就不用
    修改知识库逻辑。``k`` 控制最多返回几块；``threshold`` 负责过滤低相关度块。
    """

    # Chroma 只有真实运行检索时才需要，因此放在函数内延迟导入。
    from langchain_chroma import Chroma

    chunks = load_chunks(path)

    # Day51 使用随机 collection 名，保证重复运行互不污染；目前还不做持久化。
    vector_store = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name=f"day51-{uuid4().hex}",
    )

    # 普通 similarity 检索永远可能返回 top-k；threshold 模式允许返回空列表，
    # assistant.py 才能在证据不足时真正跳过 LLM 并拒答。
    return vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": k, "score_threshold": threshold},
    )
