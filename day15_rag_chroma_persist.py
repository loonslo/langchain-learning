"""
Day 15 · 向量库持久化：把 FAISS 换成 Chroma
==========================================================
测试工程师转 AI 应用开发

前面的 RAG 每次运行都要重新 embedding 建库，程序一关就没了。真实应用里文档不常变，
应该"建一次库、落盘保存"，之后直接加载。这节把内存版 FAISS 换成自带持久化的 Chroma。

知识点：
1. Chroma 的 persist_directory：把向量库存到硬盘
2. 建库 vs 加载：第一次建库落盘，之后直接读，不再重复 embedding
3. FAISS（内存，需手动 save_local）和 Chroma（自带持久化）怎么选

依赖：pip install langchain-chroma
==========================================================
"""

import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()
MODEL_PATH = r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-small-zh-v1___5"
PERSIST_DIR = "chroma_db"   # 向量库落盘目录，建好后会出现在当前文件夹下


def build_or_load(file_path="test_doc.txt"):
    """有落盘目录就直接加载，没有就建库并落盘。"""
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_PATH)

    # 关键点：第二次运行发现目录已存在，直接加载，省掉重新 embedding 的时间
    if os.path.exists(PERSIST_DIR):
        print(f"发现已有向量库 {PERSIST_DIR}/，直接加载（不重新 embedding）")
        return Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)

    print("首次运行：加载 → 切割 → 向量化 → 落盘")
    with open(file_path, encoding="utf-8") as f:
        text = f.read()
    docs = [Document(page_content=text, metadata={"source": os.path.basename(file_path)})]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300, chunk_overlap=50,
        separators=["\n\n", "\n", "。", "，", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    # from_documents 传入 persist_directory：建库的同时自动落盘
    return Chroma.from_documents(chunks, embeddings, persist_directory=PERSIST_DIR)


if __name__ == "__main__":
    vs = build_or_load()
    print("\n检索演示：")
    for doc in vs.similarity_search("RAG 是什么", k=3):
        print("-", doc.page_content[:50])
    print(f"\n再跑一次本脚本，会直接加载 {PERSIST_DIR}/，不再重新 embedding。")


# ----------------------------------------------------------
# 小结：
# - Chroma 自带持久化，persist_directory 指定落盘位置
# - "建一次库、之后加载"，省掉每次重复 embedding 的时间
# - FAISS 轻量、适合小项目和内存场景；Chroma 适合要持久化、要增量更新的场景
# - 更大规模/生产可了解 pgvector、Milvus（属于【了解】，用到再深入）
#
# 动手练习：跑两次本脚本，对比第一次和第二次的启动速度差异
# ----------------------------------------------------------
