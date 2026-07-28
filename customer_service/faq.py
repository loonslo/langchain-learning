"""
customer_service/faq.py · FAQ 检索问答：BM25 轻量版（复用 Day14 混合检索的一半）
==========================================================
为什么先用 BM25 不上向量库：FAQ 文档量小、查询词面重合度高，BM25 够用且零依赖
（不用加载 bge 模型），CI 里秒级可跑。文档量上来后换 capstone.KnowledgeBase
（向量+BM25 混合）即可，接口不变——这就是"先跑通再升级"的工程取舍。

离线模式：直接返回最相关 FAQ 原文；在线模式：RAG 生成 + 防过度拒答 prompt。
==========================================================
"""

from functools import lru_cache

import config as C


def _tokenize_zh(text: str) -> list[str]:
    """中文分词（字符 bigram）：BM25 默认按空格分词，中文整句会变成一个 token，
    检索直接失效（day14/capstone 里因为有向量兜底没暴露这个坑）。
    bigram 零依赖够用；要更准可换 jieba.lcut。"""
    text = "".join(text.split())
    return [text[i:i + 2] for i in range(len(text) - 1)] or [text]


@lru_cache(maxsize=1)
def _retriever():
    from langchain_community.retrievers import BM25Retriever
    from langchain_core.documents import Document

    text = C.FAQ_FILE.read_text(encoding="utf-8")
    # 按 "## " 标题切条：一条 FAQ 一个 chunk，天然语义边界（比定长切割更适合 FAQ）
    chunks = [c.strip() for c in text.split("## ") if c.strip()]
    docs = [Document(page_content=c, metadata={"source": C.FAQ_FILE.name}) for c in chunks]
    r = BM25Retriever.from_documents(docs, preprocess_func=_tokenize_zh)
    r.k = 2
    return r


def retrieve(question: str):
    return _retriever().invoke(question)


def answer(question: str, history_text: str = "") -> str:
    docs = retrieve(question)
    context = "\n---\n".join(d.page_content for d in docs)

    if C.OFFLINE:
        top = docs[0].page_content if docs else ""
        return f"（离线FAQ）{top}" if top else "抱歉，FAQ 里没有找到相关内容，我帮您转人工。"

    from langchain_core.messages import HumanMessage, SystemMessage
    llm = C.get_llm()
    msg = llm.invoke([
        SystemMessage(content=(
            "你是电商客服。只根据下面 FAQ 资料回答，答不了就说'FAQ 未涉及，建议转人工'，"
            "不要编造。回答末尾标注来源标题。\n\nFAQ 资料：\n" + context
        )),
        HumanMessage(content=(f"历史对话：\n{history_text}\n\n" if history_text else "")
                     + f"用户问题：{question}"),
    ])
    return msg.content
