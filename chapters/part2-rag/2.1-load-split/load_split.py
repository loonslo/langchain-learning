"""
章节 2.1 · 加载文档并切成片段
==========================================================
RAG（检索增强生成）：模型不知道你的私有文档，所以先从文档里检索相关内容，
再让模型基于这些内容回答。完整流程分两段：
  建库：加载 → 切分 → 向量化 → 存储
  问答：检索 → 拼接上下文 → 生成
本章只做建库的前两步；2.2 做向量化，2.3 串成完整问答。

知识点：
1. 把文件读成 LangChain 的 Document（正文 + 元数据）
2. 为什么要切块：文档太长，切成小段才方便检索
3. chunk_size 与 chunk_overlap 如何影响片段

运行：python tools/run_chapter.py 2.1 load_split.py（离线，不调用模型）
输出：示例文档的加载预览，以及每个片段的序号、字数和内容
==========================================================
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from common import LONG_DOC

# ---------- 1. 加载文档 ----------
# 示例是 chapters/shared-data/long_article.txt（一篇约 8.7KB 的长文章，路径由 common.py 提供）。
# txt 直接用 open() 读取，再自己包成 Document，不需要额外的加载器依赖；
# PDF、CSV 等格式才需要对应的 loader，见 load_split_formats.py。
with open(LONG_DOC, encoding="utf-8") as f:
    text = f.read()

# Document 是 LangChain 里文档的标准结构：page_content 是正文，metadata 存来源等信息
docs = [Document(page_content=text, metadata={"source": LONG_DOC.name})]
print(f"加载了 {len(docs)} 个文档，正文预览：{docs[0].page_content[:50]}...\n")


# ---------- 2. 切割成块 ----------
# 为什么切？一份长文档直接丢给模型，又贵又容易抓不准重点。
# 切成小块后，检索时只挑出最相关的几块喂给模型，又准又省 token。
#
# RecursiveCharacterTextSplitter 的 "Recursive"：按 separators 顺序优先级递归切——
#   先按段落 \n\n，不行再按行 \n，再按句号、逗号，最后才逐字符。
#   顺序很关键，"" 必须放最后，否则还没轮到标点就被逐字符硬切了。
#   这组中文分隔符在后续章节统一为 common.ZH_SEPARATORS。
splitter = RecursiveCharacterTextSplitter(
    chunk_size=120,        # 每块大约多少字
    chunk_overlap=20,      # 相邻块重叠多少字，防止把一句话从中间切断、丢上下文
    separators=["\n\n", "\n", "。", "，", " ", ""],
)

chunks = splitter.split_documents(docs)   # 切分时 metadata 会复制到每个片段
print(f"切成了 {len(chunks)} 块：\n")
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
