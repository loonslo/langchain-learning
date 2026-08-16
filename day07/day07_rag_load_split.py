"""
Day 7 · RAG 第一步：加载文档 + 切割成块
==========================================================
测试工程师转 AI 应用开发

从这节起进入 RAG（检索增强生成）。一句话理解 RAG：
  大模型不知道你的私有文档（公司手册、内部 wiki），
  RAG 就是"先从你的文档里检索相关内容，再让模型基于这些内容回答"。

完整 RAG 分两段：建库（加载→切割→向量化→存）和 问答（检索→拼接→生成）。
这节先做建库的前两步：加载、切割。Day8 做向量化，Day9 拼成完整问答。

知识点：
1. 怎么把文件读成 LangChain 的 Document
2. 为什么要"切块"（chunk）：文档太长，要切成小段才好检索
3. chunk_size 和 chunk_overlap 怎么影响切块
==========================================================
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------- 1. 加载文档 ----------
# 注意：早期教程常用 langchain_community 的 TextLoader，但该包已被官方 sunset，
#       会报弃用警告。最省事的做法是直接 open() 读文件，自己包成 Document，
#       langchain_core 不受影响、无警告。
with open("test_doc.txt", encoding="utf-8") as f:
    text = f.read()

# Document 是 LangChain 里文档的标准结构：page_content 是正文，metadata 存来源等信息
docs = [Document(page_content=text, metadata={"source": "test_doc.txt"})]
print(f"加载了 {len(docs)} 个文档，正文预览：{docs[0].page_content[:50]}...\n")


# ---------- 2. 切割成块 ----------
# 为什么切？一份长文档直接丢给模型，又贵又容易抓不准重点。
# 切成小块后，检索时只挑出最相关的几块喂给模型，又准又省 token。
#
# RecursiveCharacterTextSplitter 的 "Recursive"：按 separators 顺序优先级递归切——
#   先按段落 \n\n，不行再按行 \n，再按句号、逗号，最后才逐字符。
#   顺序很关键，"" 必须放最后，否则还没轮到标点就被逐字符硬切了。
splitter = RecursiveCharacterTextSplitter(
    chunk_size=120,        # 每块大约多少字
    chunk_overlap=20,      # 相邻块重叠多少字，防止把一句话从中间切断、丢上下文
    separators=["\n\n", "\n", "。", "，", " ", ""],
)

chunks = splitter.split_documents(docs)
print(f"切成了 {len(chunks)} 块：\n")
print(chunks)
for i, chunk in enumerate(chunks, 1):
    print(f"--- 块 {i}（{len(chunk.page_content)} 字）---")
    print(chunk.page_content)
    print()


# ----------------------------------------------------------
# 小结：
# - RAG = 先检索你的文档、再让模型基于检索内容回答
# - 文档要先切块，检索才能精准、省钱
# - chunk_size 太大 → 块里夹杂无关内容；太小 → 一句话被切碎、丢语境
# - chunk_overlap 让相邻块有重叠，缓解"切断语义"的问题
#
# 动手练习：把 chunk_size 改成 50 和 300 各跑一次，对比块数和每块的完整度
# ----------------------------------------------------------
