"""
Day 13 · 混合检索：向量 + BM25 关键词
==========================================================
测试工程师转 AI 应用开发

向量检索擅长"语义相近"，但对专有名词、编号、型号这种"必须精确匹配"的词
常常召回不准（比如问"FAISS"，它可能给你一堆"向量库"的近义内容却漏了正主）。
BM25 是经典的关键词检索，正好和向量互补。这节把两者合起来（hybrid）。

知识点：
1. BM25Retriever：基于关键词频率的检索（不靠 embedding）
2. EnsembleRetriever：按权重合并多个检索器的结果
3. 为什么专有名词向量召回差、混合怎么救

依赖：pip install rank_bm25
注意（langchain 1.x）：EnsembleRetriever 已从 langchain.retrievers 迁到 langchain_classic.retrievers。
==========================================================
"""

import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from common import get_embeddings, ZH_SEPARATORS


def build_retrievers(path="test_doc.txt"):
    """建三种检索器：纯向量、纯 BM25、混合。返回 (向量, 混合) 供对比。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    docs = [Document(page_content=text, metadata={"source": os.path.basename(path)})]
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=120, chunk_overlap=20, separators=ZH_SEPARATORS,
    ).split_documents(docs)

    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # 1) 向量检索：靠语义相似度
    vector_ret = vectorstore.as_retriever(search_kwargs={"k": 4})

    # 2) BM25 检索：靠关键词匹配，直接从 chunks 构建，不需要 embedding
    bm25_ret = BM25Retriever.from_documents(chunks)
    bm25_ret.k = 4

    # 3) 混合检索：EnsembleRetriever 把两者结果按权重融合
    #    weights=[0.5, 0.5] 表示两者各占一半，可按场景调（专有名词多就给 BM25 高一点）
    hybrid_ret = EnsembleRetriever(retrievers=[vector_ret, bm25_ret], weights=[0.5, 0.5])
    return vector_ret, hybrid_ret


if __name__ == "__main__":
    vector_ret, hybrid_ret = build_retrievers()

    # 对比：含专有名词的查询，纯向量 vs 混合
    query = "FAISS 有什么作用"
    print(f"查询：{query}\n")

    print("【纯向量检索】")
    for d in vector_ret.invoke(query):
        print(" -", d.page_content[:40])

    print("\n【混合检索（向量 + BM25）】")
    for d in hybrid_ret.invoke(query):
        print(" -", d.page_content[:40])


# ----------------------------------------------------------
# 小结：
# - 向量检索懂语义但对精确词（专有名词/编号）不敏感；BM25 正好补上
# - EnsembleRetriever 按权重融合多路检索；权重要按你的文档/问题类型调
# - 判断要不要混合：如果你的领域有大量型号、缩写、编号，混合通常明显更好
#
# 动手练习：把一个含具体编号/英文缩写的问题分别用 vector_ret 和 hybrid_ret 跑，
#          看混合是不是把那条"精确命中"的块捞回来了
# ----------------------------------------------------------
