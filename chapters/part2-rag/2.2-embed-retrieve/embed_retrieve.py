"""
章节 2.2 · 向量化与语义检索
==========================================================
2.1 把文档切成了块。本章解决一个核心问题：
  怎么从一堆块里，找出和"用户问题"最相关的几块？
答案是语义检索：把文字变成向量（一串数字），再比较谁的向量最接近。

知识点：
1. Embedding（向量化）：把文字变成能比较语义的向量
2. 向量库 FAISS：存放所有块的向量，支持"找最相似的 k 个"
3. similarity_search：输入问题，召回最相关的块

前置：2.1；本地 embedding 模型（下载方法见根目录 README"准备本地 embedding 模型"）；faiss-cpu
运行：python tools/run_chapter.py 2.2（离线，不调用聊天模型）
输出：切块数、一个片段的向量维度，以及三个问题各自召回的 3 个片段
==========================================================
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
# 注：langchain-community 仓库已于 2026-06 归档停止维护（官方 issue #674），FAISS 暂无独立
# 集成包，仍从这里导入。LangChain v1 的方向是一个供应商一个包（langchain-chroma、
# langchain-openai 等），旧接口归入 langchain-classic。
from langchain_community.vectorstores import FAISS

from common import EMBED_MODEL_PATH, SAMPLE_DOC

# ---------- 1. 加载 + 切割（复用 2.1 的做法）----------
with open(SAMPLE_DOC, encoding="utf-8") as f:
    text = f.read()
docs = [Document(page_content=text, metadata={"source": SAMPLE_DOC.name})]
splitter = RecursiveCharacterTextSplitter(
    chunk_size=120, chunk_overlap=20,
    separators=["\n\n", "\n", "。", "，", " ", ""],
)
chunks = splitter.split_documents(docs)
print(f"切割后共 {len(chunks)} 块\n")


# ---------- 2. 加载 Embedding 模型 ----------
# Embedding 模型负责把文字变成向量。这里用中文小模型 bge-small-zh-v1.5（约 100MB）。
#
# 下载方式（国内推荐用魔搭 ModelScope，免代理）：
#   from modelscope import snapshot_download
#   model_dir = snapshot_download('BAAI/bge-small-zh-v1.5')
#   print(model_dir)   # 把打印出的路径写进 .env 的 EMBED_MODEL_PATH
#
# 注意：ModelScope 缓存目录里的点号会被换成下划线，
#       实际路径形如 ...bge-small-zh-v1___5（三个下划线）。
# 路径来自 common.EMBED_MODEL_PATH：默认指向 ModelScope 缓存目录，换机器时用环境变量覆盖。
embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL_PATH)

# 看一段文字被变成了什么样的向量
vec = embeddings.embed_query(chunks[0].page_content)
print(f"向量维度：{len(vec)}（bge-small-zh 固定 512 维，与文字长短无关）")
print(f"前 5 个数字：{vec[:5]}\n")


# ---------- 3. 存进 FAISS，做语义检索 ----------
# FAISS 不是数据库，是个"高维向量找最近邻"的索引库。
# from_documents 会把每个块向量化后存进索引。
vectorstore = FAISS.from_documents(chunks, embeddings)

# similarity_search(问题, k)：把问题也转成向量，找出最相似的 k 个块。
# 关键点：它比的是"语义"而非"关键词"——问"怎么存储向量"也能命中讲 FAISS 的块。
# 注意：无论资料里有没有答案，它都会返回 k 个块；检索本身不会说"没有"。
for query in ["RAG 是什么", "LangGraph 有什么用", "怎么存储向量"]:
    print(f"========== 查询：{query} ==========")
    for i, doc in enumerate(vectorstore.similarity_search(query, k=3), 1):
        print(f"[{i}] {doc.page_content[:60]}")
    print()


# ----------------------------------------------------------
# 小结：
# - Embedding 把文字映射成固定维度的向量，向量近 = 语义近
# - FAISS 存向量、做"找最相似的 k 个块"
# - k 是关键调参：太小可能漏掉相关块，太大会塞进无关内容、稀释信息
#
# 提醒：这里的 FAISS 只建在内存里，程序一结束就没了。要持久化可用
#       vectorstore.save_local("faiss_index")，也可换成 Chroma（自带落盘，见 2.10）。
#
# 动手练习：把 k 从 3 改成 1 和 6，看召回的块怎么变
# ----------------------------------------------------------
