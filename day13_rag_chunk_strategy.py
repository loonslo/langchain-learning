"""
Day 13 · RAG 进阶：chunk 切割策略对比
==========================================================
测试工程师转 AI 应用开发

RAG 答得准不准，第一道关口不是模型，是"文档切得好不好"。切得太碎，
一个完整意思被劈成两半，检索只拿到半句；切得太大，一个块里塞了无关内容，
噪声把关键信息淹了。这节不引入新组件，只调切割参数，用同一个问题观察
检索结果怎么变——把"凭感觉设 chunk_size"变成"看效果调"。

知识点：
1. chunk_size：每块多大。小=精准但易断意，大=完整但带噪声
2. chunk_overlap：相邻块重叠多少字，防止"答案正好被切在边界"
3. separators：按什么优先级切（段落 > 换行 > 句号…），中文要自己配（见 common.ZH_SEPARATORS）
4. 同一问题在不同切法下，检索召回的块差异
==========================================================
"""

import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from common import get_embeddings, ZH_SEPARATORS

# ---------- 三组对照参数：每组改一个变量，单变量对比才看得清影响 ----------
STRATEGIES = [
    {"name": "小块 + 无重叠", "chunk_size": 50, "chunk_overlap": 0},
    {"name": "小块 + 有重叠", "chunk_size": 50, "chunk_overlap": 20},
    {"name": "大块 + 有重叠", "chunk_size": 200, "chunk_overlap": 30},
]

QUERY = "RAG 为什么能减少幻觉"  # 答案横跨"检索相关文档→基于片段回答"两小句，最考验切割


def load_docs(path="test_doc.txt"):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return [Document(page_content=text, metadata={"source": os.path.basename(path)})]


def run_strategy(cfg: dict, docs, embeddings):
    """按一组参数切割、建库、检索，打印块数和召回结果。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg["chunk_size"],
        chunk_overlap=cfg["chunk_overlap"],
        separators=ZH_SEPARATORS,
    )
    chunks = splitter.split_documents(docs)
    vs = FAISS.from_documents(chunks, embeddings)
    hits = vs.as_retriever(search_kwargs={"k": 2}).invoke(QUERY)

    print(f"\n【{cfg['name']}】size={cfg['chunk_size']} overlap={cfg['chunk_overlap']}")
    print(f"  切出 {len(chunks)} 块，平均每块 {sum(len(c.page_content) for c in chunks)//len(chunks)} 字")
    for i, d in enumerate(hits, 1):
        print(f"  召回{i}: {d.page_content.strip()[:60]}")


if __name__ == "__main__":
    # embedding 只建一次，重复用（建库才是变量，embedding 模型是常量）
    docs = load_docs()
    embeddings = get_embeddings()
    print(f"问题：{QUERY}")
    for cfg in STRATEGIES:
        run_strategy(cfg, docs, embeddings)

# ----------------------------------------------------------
# 怎么读结果：
# - 小块无重叠：块多、精准，但"检索相关文档"和"基于片段回答"可能被切到两块，
#   只召回一半 → 答案不全。
# - 小块有重叠：边界处的句子在相邻块各留一份，跨边界的意思更容易被一块兜住。
# - 大块有重叠：单块信息全，但也更容易混进无关句子（噪声），且更费 token。
#
# 经验起点（再按评测调）：中文 chunk_size 300-500、overlap 取 size 的 10-20%。
# 没有万能值——这正是 Day17+ 评测的意义：用数字证明"哪种切法答得更准"。
#
# 动手练习：
# 1) 把 QUERY 换成只在单句里的事实问题（如"LangGraph 是什么"），看切法影响是否变小。
# 2) 加一组"超大块 size=500 overlap=0"，观察召回里混进多少无关内容。
# ----------------------------------------------------------
