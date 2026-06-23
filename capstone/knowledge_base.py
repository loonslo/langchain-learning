"""
capstone/knowledge_base.py · 知识库：加载 → 切割 → 混合检索 → 带溯源问答
==========================================================
整合 day11-16：多格式加载 + metadata 溯源 + 混合检索(向量+BM25)
+ Chroma 持久化 + 防过度拒答的 prompt。对外暴露 KnowledgeBase 类。
==========================================================
"""

import os
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

import config as C


def _load_one(path: Path) -> list[Document]:
    ext = path.suffix.lower()
    if ext in (".txt", ".md"):
        return [Document(page_content=path.read_text(encoding="utf-8"),
                         metadata={"source": path.name})]
    if ext == ".pdf":
        from pypdf import PdfReader
        docs = []
        for i, page in enumerate(PdfReader(str(path)).pages, 1):
            t = page.extract_text() or ""
            if t.strip():
                docs.append(Document(page_content=t,
                                     metadata={"source": path.name, "page": i}))
        return docs
    return []


class KnowledgeBase:
    def __init__(self):
        self.embeddings = C.get_embeddings()
        self.chunks: list[Document] = []
        self.vectorstore = None
        self.retriever = None

    def build(self, rebuild: bool = False):
        """从 docs/ 建库；已落盘则直接加载（除非 rebuild=True）。"""
        if os.path.exists(C.CHROMA_DIR) and not rebuild:
            self.vectorstore = Chroma(persist_directory=C.CHROMA_DIR,
                                      embedding_function=self.embeddings)
            print(f"加载已有向量库 {C.CHROMA_DIR}")
        else:
            docs = []
            for p in sorted(C.DOCS_DIR.glob("*")):
                docs += _load_one(p)
            if not docs:
                raise ValueError(f"{C.DOCS_DIR} 里没有可用文档（放 txt/md/pdf）")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=C.CHUNK_SIZE, chunk_overlap=C.CHUNK_OVERLAP,
                separators=C.ZH_SEPARATORS)
            self.chunks = splitter.split_documents(docs)
            self.vectorstore = Chroma.from_documents(
                self.chunks, self.embeddings, persist_directory=C.CHROMA_DIR)
            print(f"建库完成：{len(self.chunks)} 块，已落盘 {C.CHROMA_DIR}")

        # 混合检索：向量 + BM25（BM25 需要 chunk 列表，缺则退回纯向量）
        vector_ret = self.vectorstore.as_retriever(search_kwargs={"k": C.TOP_K})
        if self.chunks:
            bm25 = BM25Retriever.from_documents(self.chunks); bm25.k = C.TOP_K
            self.retriever = EnsembleRetriever(retrievers=[vector_ret, bm25],
                                               weights=[0.5, 0.5])
        else:
            self.retriever = vector_ret
        return self

    def _format(self, docs):
        parts = []
        for d in docs:
            src = d.metadata.get("source", "未知")
            page = d.metadata.get("page")
            tag = f"[来源：{src}" + (f" 第{page}页]" if page else "]")
            parts.append(f"{tag}\n{d.page_content}")
        return "\n\n".join(parts)

    def chain(self, temperature: float = 0.0):
        llm = C.get_llm(temperature=temperature)
        prompt = ChatPromptTemplate.from_template(
            "你是严谨的知识库助手，依据上下文回答：\n"
            "- 有相关信息（哪怕部分）就尽量答，并在结尾用【来源】标注；\n"
            "- 完全无相关信息才回答'文档中没有提到'。\n\n"
            "上下文：\n{context}\n\n问题：{question}")
        return ({"context": self.retriever | self._format,
                 "question": RunnablePassthrough()}
                | prompt | llm | StrOutputParser())

    def answer(self, question: str) -> str:
        return self.chain().invoke(question)


if __name__ == "__main__":
    kb = KnowledgeBase().build()
    print("\n问答演示：")
    print(kb.answer("这个知识库讲了什么？")[:200])
