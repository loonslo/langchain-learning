"""
章节 2.6 · 处理 PDF 并标注来源
==========================================================
2.3 的最小 RAG 只能读一个 txt，写法是平铺的。真实场景里文档常是 PDF，
用户也会追问"这个答案出自哪里"。本章把 RAG 升级为可复用的形式：

1. 支持 txt 和 pdf，统一加载
2. 给每个块打 metadata（来源文件、页码），回答时能标出处
3. 把"建库"和"问答链"封装成函数——可复用、也方便后面写测试
4. 改进 prompt：有部分相关信息就尽量答，完全无关才拒答
   （修掉最小 RAG 常见的"过度拒答"：明明检索到了相关内容却说不知道）

知识点：metadata 溯源、prompt 措辞对"拒答 vs 过度拒答"的影响、模块化封装
（模型路径和 LLM 初始化已抽到 common.py，换机器只改那一处）

前置：2.3；DEEPSEEK_API_KEY；本地 embedding 模型；读 PDF 需要 pypdf
运行：python tools/run_chapter.py 2.6（交互式，直接回车使用示例文档）
被复用：3.2、3.3、3.5、3.6、3.7、5.8 会导入本文件的 build_retriever / build_rag_chain
==========================================================
"""

import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from common import SAMPLE_DOC, get_embeddings, get_llm, ZH_SEPARATORS


def load_document(file_path: str) -> list[Document]:
    """支持 .txt 和 .pdf，统一返回 Document 列表，并带上来源 metadata。"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, encoding="utf-8") as f:
            text = f.read()
        return [Document(page_content=text,
                         metadata={"source": os.path.basename(file_path)})]
    elif ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        docs = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():   # 跳过空页：扫描件没有文字层，extract_text 会返回空
                docs.append(Document(
                    page_content=text,
                    metadata={"source": os.path.basename(file_path), "page": i},
                ))
        return docs
    else:
        raise ValueError(f"暂不支持的文件类型：{ext}")


def build_retriever(file_path: str):
    """加载 → 切割 → 向量化 → 返回检索器。封装成函数，复用和测试都方便。"""
    docs = load_document(file_path)
    if not docs:
        raise ValueError("没解析出任何文本（PDF 可能是扫描件，没有文字层）")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300, chunk_overlap=50, separators=ZH_SEPARATORS,
    )
    chunks = splitter.split_documents(docs)   # 切割会自动把 metadata 带到每个块上
    print(f"共切成 {len(chunks)} 块")

    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 4})


def build_rag_chain(retriever, temperature: float = 0.0):
    """组装 RAG 链。prompt 措辞经过改进，避免'过度拒答'。

    temperature 默认 0：3.2、3.3、3.6 等章节会把这条链当作"被测对象"反复运行，
    结果必须可复现，回归测试才有意义。"""
    llm = get_llm(temperature=temperature)

    def format_docs(docs):
        # 把来源信息一并拼进上下文，模型才有依据标出处
        parts = []
        for d in docs:
            src = d.metadata.get("source", "未知")
            page = d.metadata.get("page")
            tag = f"[来源：{src}" + (f" 第{page}页]" if page else "]")
            parts.append(f"{tag}\n{d.page_content}")
        return "\n\n".join(parts)

    # 对比 2.3："没答案就说不知道"太严，会把"部分相关"也拒掉。
    # 这里改成：有部分信息就基于它尽量答并标来源，完全无关才拒答。
    prompt = ChatPromptTemplate.from_template("""
        你是严谨的知识库助手。请依据下面的上下文回答问题：
        - 只要有相关信息（哪怕只是部分），就基于它尽量回答，并在结尾用【来源】标注出处；
        - 只有完全没有相关信息时，才回答"文档中没有提到"。
        
        上下文：
        {context}
        
        问题：
        {question}
        """)

    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt | llm | StrOutputParser()
    )


if __name__ == "__main__":
    path = input("输入文件路径（.txt 或 .pdf，直接回车使用示例文档）：").strip() or str(SAMPLE_DOC)
    retriever = build_retriever(path)
    rag_chain = build_rag_chain(retriever)
    print("知识库就绪，输入问题（q 退出）")
    while True:
        q = input("\n问题：").strip()
        if q.lower() == "q":
            break
        print("回答：", rag_chain.invoke(q))


# ----------------------------------------------------------
# 小结：
# - 真实 RAG 要能处理 PDF、能溯源、封装好便于复用和测试
# - metadata（来源/页码）跟着 chunk 一路带到回答里，是"可信问答"的基础
# - prompt 措辞直接影响"拒答 vs 过度拒答"，是 RAG 调优里最便宜的旋钮
# - build_rag_chain 默认 temperature=0：被评测反复调用时结果可复现
#
# 动手练习：找一份带页码的真实 PDF（产品手册/合同），问一个跨页的问题，
#          看回答能不能正确标出"第几页"。
# ----------------------------------------------------------
