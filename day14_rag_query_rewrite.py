"""
Day 14 · 查询改写：Multi-Query 与 HyDE
==========================================================
测试工程师转 AI 应用开发

用户问得短、用的词和文档里不一样时，检索容易漏。两个常用补救手段：
- Multi-Query：让 LLM 把一个问题改写成多条不同说法，分别检索再合并，覆盖更全
- HyDE：先让 LLM 生成一个"假设答案"，拿这个答案去检索
        （答案的措辞通常和文档更接近，比原始短问题更容易命中）

知识点：
1. MultiQueryRetriever（LangChain 内置）
2. HyDE 的思路 + 手写实现（就几行，理解原理更重要）
==========================================================
"""

import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever

load_dotenv()
MODEL_PATH = r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-small-zh-v1___5"

# ---------- 建库 ----------
with open("test_doc.txt", encoding="utf-8") as f:
    text = f.read()
docs = [Document(page_content=text, metadata={"source": "test_doc.txt"})]
splitter = RecursiveCharacterTextSplitter(
    chunk_size=120, chunk_overlap=20,
    separators=["\n\n", "\n", "。", "，", " ", ""],
)
chunks = splitter.split_documents(docs)
embeddings = HuggingFaceEmbeddings(model_name=MODEL_PATH)
vectorstore = FAISS.from_documents(chunks, embeddings)
base_ret = vectorstore.as_retriever(search_kwargs={"k": 3})

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

query = "向量怎么存"


# ---------- 方法一：Multi-Query ----------
# MultiQueryRetriever 会让 llm 把原问题改写成多条（如"如何存储向量""向量持久化方式"），
# 各自检索后把结果去重合并，召回更全。
multi_ret = MultiQueryRetriever.from_llm(retriever=base_ret, llm=llm)

print("【原始问题直接检索】")
for d in base_ret.invoke(query):
    print(" -", d.page_content[:40])

print("\n【Multi-Query 改写后检索】")
for d in multi_ret.invoke(query):
    print(" -", d.page_content[:40])


# ---------- 方法二：HyDE（手写，理解原理）----------
# 先让 llm 对问题"瞎答"一个假设答案（哪怕不准），再用这个答案去检索。
# 因为答案的措辞更像文档正文，往往比原始短问题更容易命中相关块。
hyde_prompt = ChatPromptTemplate.from_template(
    "请用两三句话假设性地回答下面的问题（不确定也照写，用于检索）：\n{question}"
)
hyde_chain = hyde_prompt | llm | StrOutputParser()

hypo_answer = hyde_chain.invoke({"question": query})
print(f"\n【HyDE 生成的假设答案】\n{hypo_answer}")

print("\n【用假设答案去检索】")
for d in base_ret.invoke(hypo_answer):
    print(" -", d.page_content[:40])


# ----------------------------------------------------------
# 小结：
# - Multi-Query：一题多问，覆盖不同说法，召回更全（代价是多调几次 LLM）
# - HyDE：先生成假设答案再检索，让"问题"在措辞上更靠近"文档"
# - 都属于"用 LLM 改善检索召回"，适合用户问得短/口语化的场景
#
# 提醒：这些都会增加 LLM 调用次数（更慢更贵），要按效果权衡是否开启。
#
# 动手练习：故意问一个很口语、很短的问题，对比三种方式（原始/Multi-Query/HyDE）
#          的召回差异
# ----------------------------------------------------------
