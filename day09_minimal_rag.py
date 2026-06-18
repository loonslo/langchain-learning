"""
Day 9 · 最小 RAG：把检索和生成串成完整问答
==========================================================
测试工程师转 AI 应用开发

Day7 切块、Day8 向量化检索。这节补上最后一步——把"检索到的内容"喂给模型，
让它基于这些内容回答，并在文档没答案时老实说"不知道"。这就是一个完整的最小 RAG。

知识点：
1. retriever：把向量库包装成"可插拔的检索器"，还能用 MMR 提升结果多样性
2. 用 LCEL 把 检索 → 拼接 → 提示 → 模型 → 取文本 串成一条链
3. RunnableParallel（字典写法）和 RunnablePassthrough 是怎么配合的
4. 怎么用 prompt 抑制幻觉（没检索到就拒答）
==========================================================
"""

import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()

# ---------- 1. 建库：加载 → 切割 → 向量化（Day7 + Day8 的合并）----------
# 加载用 open() + Document，避开 langchain_community 里 TextLoader 的弃用警告
with open("test_doc.txt", encoding="utf-8") as f:
    text = f.read()
docs = [Document(page_content=text, metadata={"source": "test_doc.txt"})]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=120, chunk_overlap=20,
    separators=["\n\n", "\n", "。", "，", " ", ""],
)
chunks = splitter.split_documents(docs)

MODEL_PATH = r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-small-zh-v1___5"
embeddings = HuggingFaceEmbeddings(model_name=MODEL_PATH)
vectorstore = FAISS.from_documents(chunks, embeddings)


# ---------- 2. 检索器：这次用 MMR 提升多样性 ----------
# as_retriever 把向量库标准化成可插拔的检索组件。
# search_type="mmr"（最大边际相关性）：先粗取 fetch_k 条候选，再在"相关性"和
#   "多样性"之间权衡挑出 k 条，避免召回的几块内容高度重复、信息冗余。
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,               # 最终返回 3 条
        "fetch_k": 10,        # 先取 10 条候选再筛
        "lambda_mult": 0.5,   # 1=只看相关性，0=只看多样性，0.5 居中
    },
)


# 把检索到的多个块拼成一段上下文文本
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# ---------- 3. 提示词：限定"只根据上下文回答"，没答案就拒答（抑制幻觉）----------
prompt = ChatPromptTemplate.from_template("""
你是一个严谨的知识库问答助手。
请只根据下面的上下文回答问题。如果上下文里没有答案，就说：我不知道。

上下文：
{context}

问题：
{question}
""")

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


# ---------- 4. 用 LCEL 组装完整 RAG 链 ----------
# 开头那个字典就是 RunnableParallel（并行）：输入的问题同时走两条路——
#   context 路：问题 → retriever 检索 → format_docs 拼成文本
#   question 路：问题 → RunnablePassthrough() 原样透传
# 两路汇成 {"context": ..., "question": ...}，再依次进 prompt → llm → 取纯文本。
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)


# ---------- 5. 测试：3 个文档相关问题 + 1 个无关问题（验证拒答）----------
questions = [
    "RAG 是什么？",
    "Embedding 是干嘛的？",
    "FAISS 有什么作用？",
    "今天天气怎么样？",   # 文档里没有 → 应该回答"我不知道"
]
for q in questions:
    print("=" * 40)
    print("问题：", q)
    print("回答：", rag_chain.invoke(q))


# ----------------------------------------------------------
# 小结：一个完整 RAG = 检索（找相关块）+ 生成（基于块回答）
# - MMR 让召回的块更多样、信息更全
# - 字典写法 = RunnableParallel 并行，RunnablePassthrough 负责原样透传问题
# - "没答案就说不知道"这条 prompt 指令能有效抑制幻觉，是 RAG 质量的关键
#
# 下一步（进阶方向，正好是测试转 AI 的护城河）：
#   给 RAG 造评测集、量化"答错率/幻觉率"、做回归测试——这部分普通开发不会，
#   恰恰是测试背景最能打的地方。
# ----------------------------------------------------------
