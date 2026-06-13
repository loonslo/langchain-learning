import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


def load_document(file_path: str) -> list[Document]:
    """支持 .txt 和 .pdf，统一返回 Document 列表"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return [Document(page_content=text, metadata={"source": file_path})]
    elif ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        docs = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                docs.append(Document(page_content=text, metadata={"source": file_path, "page": i + 1}))
        return docs
    else:
        raise ValueError(f"不支持的文件类型: {ext}")


def build_retriever(file_path: str):
    """加载 -> 切割 -> 向量化 -> 返回 retriever"""
    docs = load_document(file_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "，", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"文档切成 {len(chunks)} 个 chunk")

    embeddings = HuggingFaceEmbeddings(
        model_name=r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-small-zh-v1___5"
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 4})


def build_rag_chain(retriever):
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    prompt = ChatPromptTemplate.from_template("""
根据以下上下文回答问题。如果上下文中有部分相关信息，请基于这些信息尽量回答，并说明信息可能不完整；如果完全没有相关信息，再说"文档中没有提到"。

上下文：
{context}

问题：{question}
""")

    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


if __name__ == "__main__":
    file_path = input("请输入文件路径（.txt 或 .pdf）：").strip()
    retriever = build_retriever(file_path)
    rag_chain = build_rag_chain(retriever)
    print('retriever')
    print(retriever)
    print('rag_chain')
    print(rag_chain)

    print("知识库已就绪，输入问题开始提问（输入 q 退出）")
    while True:
        question = input("\n问题：").strip()
        if question.lower() == "q":
            break
        print("回答：", rag_chain.invoke(question))