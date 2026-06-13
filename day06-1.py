from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 加载 + 切割（沿用 Day 8 的方式）
with open("test_doc.txt", encoding="utf-8") as f:
    text = f.read()

docs = [Document(page_content=text, metadata={"source": "test_doc.txt"})]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=50,
    chunk_overlap=10,
    separators=["\n\n", "\n", "。", "，", " ", ""]
)
chunks = splitter.split_documents(docs)
print(f"切割后共 {len(chunks)} 块\n")

# 2. 加载 embedding 模型（首次运行自动下载，约100MB）
embeddings = HuggingFaceEmbeddings(
    model_name=r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-small-zh-v1___5")  # 看看一段文字变成什么样的向量
vec = embeddings.embed_query(chunks[0].page_content)
print(f"向量维度：{len(vec)}")
print(f"前5个数字：{vec[:5]}\n")

# 3. 所有 chunk 转向量，存入 FAISS
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

query = "为这个句子生成表示以用于检索相关文章：RAG 是什么"
# 4. 语义检索：输入问题，找最相关的 chunk
for query in ["RAG 是什么", "LangGraph 有什么用", "怎么存储向量"]:
    print(f"\n========== 查询：{query} ==========")
    results = vectorstore.similarity_search(query, k=4)
    for i, doc in enumerate(results):
        print(f"[{i + 1}] {doc.page_content}")

# 复用之前的 DeepSeek 配置（如果 day05-2.py 里已有 llm，可以不用重复定义）
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


# 把检索到的 chunk 列表拼成一段文本，作为上下文
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


prompt = ChatPromptTemplate.from_template("""
根据以下上下文回答问题，如果上下文中没有相关信息，就说"文档中没有提到"。

上下文：
{context}

问题：{question}
""")

rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)

for q in ["RAG 是什么", "LangGraph 有什么用", "怎么存储向量", "这篇文档讲了Python语法吗"]:
    print(f"========== 问题：{q} ==========")
    print(rag_chain.invoke(q))
    print()
