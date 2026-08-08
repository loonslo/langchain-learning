"""把 Markdown 客服资料转换成可以按语义搜索的 Retriever。

数据流：Path → TextLoader → Document → TextSplitter → chunks → Chroma → Retriever。

这个模块只负责“准备和查找资料”，不负责组织自然语言答案。生成答案的工作位于
``assistant.py``，这样检索失败和生成失败可以分别测试、分别改进。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from src.customer_support.ingestion import ingest_directory
from src.customer_support.retrieval import HybridRetriever, KeywordRetriever


def build_retriever(
    path: Path,
    embeddings: Any,
    *,
    k: int,
    threshold: float,
    keyword_k: int | None = None,
):
    """把文档块写入内存 Chroma，并把语义检索与关键词检索融合成统一 Retriever。

    ``embeddings`` 通过参数传入，而不是在这里创建，测试或后续更换模型时就不用
    修改知识库逻辑。``k`` 控制混合检索最终返回几块；``threshold`` 负责过滤语义检索
    的低相关度块（Chroma 相似度阈值模式允许返回空列表，证据不足时 assistant 才
    能真正跳过 LLM 并拒答）；``keyword_k`` 控制关键词检索单路返回的块数。
    """

    # Chroma 只有真实运行检索时才需要，因此放在函数内延迟导入。
    from langchain_chroma import Chroma

    chunks = ingest_directory(path)

    # Day51 使用随机 collection 名，保证重复运行互不污染；目前还不做持久化。
    vector_store = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name=f"{uuid4().hex}",
    )

    # 普通 similarity 检索永远可能返回 top-k；threshold 模式允许返回空列表，
    # assistant.py 才能在证据不足时真正跳过 LLM 并拒答。
    semantic_retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": k, "score_threshold": threshold},
    )

    # 关键词检索复用同一批文档块，离线计算 BM25 统计，无需联网或向量模型。
    keyword_retriever = KeywordRetriever(
        documents=chunks, k=keyword_k if keyword_k is not None else k
    )

    # 用 RRF 把两路排序融合成一路，对外仍暴露统一的 invoke 接口。
    return HybridRetriever(
        semantic=semantic_retriever,
        keyword=keyword_retriever,
        limit=k,
    )
