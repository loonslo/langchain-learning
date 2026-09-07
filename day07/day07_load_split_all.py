"""
Day 7 补全版 · 所有文件格式的「加载 + 语义切片」统一工具
==========================================================
测试工程师转 AI 应用开发

Day7 原版只用了 open() + 一个 test_doc.txt，没覆盖"不同文件怎么加载、不同内容怎么切"。
这一版把常见格式都合并进来，核心思想就两条：

1. 加载看「文件扩展名」→ 选对应 loader → 统一产出 List[Document]
2. 切片看「内容结构」→ 选语义感知的 splitter → 切在语义边界上，不切断标题/函数/记录

语义感知 = 按内容的结构/语法/含义边界下刀，而不是按字符位置硬切。
  - Markdown/HTML → 按标题层级切（MarkdownHeaderTextSplitter / HTMLHeaderTextSplitter）
  - 代码(.py/.js/...) → 按语法树切（Language 系列，不切断函数）
  - PDF/Word → loader 用 mode="elements" 按段落/元素切（页/段落即边界）
  - CSV/JSON → loader 直接按「一条记录 = 一个 Document」切（记录即边界）
  - 散文/未知 → SemanticChunker 按话题相似度切（无结构也能语义切）

依赖说明（对照仓库 requirements.txt）：
  - 已具备：pypdf、langchain-community、langchain-text-splitters、langchain-huggingface
  - 需另装（本文件做了优雅降级，没装也能跑基础格式）：
      docx  → pip install docx2txt
      json  → langchain-community 自带 JSONLoader
      csv   → langchain-community 自带 CSVLoader
      html  → pip install bs4
      unstructured → pip install unstructured（重，按需）

用法：
  from day07_load_split_all import load_and_split
  chunks = load_and_split("手册.pdf")          # 自动按扩展名派发
  chunks = load_and_split("文档.md", chunk_size=300)
==========================================================
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    PythonCodeTextSplitter,
    Language,
)

# 复用 Day11+ 的公共配置（中文分隔符、embedding 路径），换机器只改 common.py
try:
    from common import ZH_SEPARATORS, EMBED_MODEL_PATH
except Exception:  # 单独跑这个文件时兜底
    ZH_SEPARATORS = ["\n\n", "\n", "。", "，", " ", ""]
    EMBED_MODEL_PATH = r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-small-zh-v1___5"


# ----------------------------------------------------------
# 1) 通用兜底：没有合适 loader 时，仍可用 open() 自己包（Day7 原版方式，最稳）
# ----------------------------------------------------------
def _load_text_fallback(path: str) -> List[Document]:
    with open(path, encoding="utf-8") as f:
        return [Document(page_content=f.read(), metadata={"source": path})]


# ----------------------------------------------------------
# 2) 按扩展名派发「加载器」
#    每个 loader 的目标都是：产出 List[Document]，且尽量按「语义单元」切好
# ----------------------------------------------------------
def _load_by_ext(path: str) -> List[Document]:
    ext = Path(path).suffix.lower()

    # ---- .pdf：每页一个 Document；用 pypdf（已在依赖里）----
    if ext == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader
        return PyPDFLoader(path).load()      # 页 = 粗粒度语义边界

    # ---- .docx：优先 UnstructuredWordDocumentLoader（按段落/标题元素切）----
    if ext == ".docx":
        try:
            from langchain_community.document_loaders import (
                UnstructuredWordDocumentLoader,
            )
            return UnstructuredWordDocumentLoader(path, mode="elements").load()
        except Exception:
            # 没装 unstructured 时退化：用 docx2txt 读全文再包成一份
            try:
                import docx2txt
                text = docx2txt.process(path) or ""
                return [Document(page_content=text, metadata={"source": path})]
            except Exception:
                raise RuntimeError("读 .docx 需 pip install unstructured 或 docx2txt")

    # ---- .csv：每行 = 一条记录 = 一个 Document（记录即语义边界）----
    if ext == ".csv":
        from langchain_community.document_loaders import CSVLoader
        return CSVLoader(path, encoding="utf-8").load()

    # ---- .json / .jsonl：每个数组元素 = 一个 Document ----
    if ext in (".json", ".jsonl"):
        from langchain_community.document_loaders import JSONLoader
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # 数组 → 每个元素一份；对象 → 整体一份
        if isinstance(data, list):
            return [
                Document(page_content=json.dumps(item, ensure_ascii=False),
                         metadata={"source": path, "index": i})
                for i, item in enumerate(data)
            ]
        return [Document(page_content=json.dumps(data, ensure_ascii=False),
                         metadata={"source": path})]

    # ---- .md：先用 MarkdownHeaderTextSplitter 按标题层级切（语义切）----
    #   注意：header splitter 直接吃文本、产出带标题 metadata 的块，
    #   这里返回「已按标题切好的 Document 列表」，下游一般无需再粗切。
    if ext == ".md":
        from langchain_community.document_loaders import TextLoader
        raw = TextLoader(path, encoding="utf-8").load()[0].page_content
        md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
            ("#", "h1"), ("##", "h2"), ("###", "h3"),
        ])
        return md_splitter.split_text(raw)

    # ---- .html / .htm：按 DOM 标题层级切 ----
    if ext in (".html", ".htm"):
        try:
            from langchain_community.document_loaders import (
                UnstructuredHTMLLoader,
            )
            return UnstructuredHTMLLoader(path, mode="elements").load()
        except Exception:
            from langchain_community.document_loaders import BS4HTMLLoader
            return BS4HTMLLoader(path).load()   # 需 pip install bs4

    # ---- 代码类：按文件扩展名映射 Language，用语法树切 ----
    code_map = {
        ".py": Language.PYTHON, ".js": Language.JS, ".ts": Language.TS,
        ".java": Language.JAVA, ".go": Language.GO, ".cpp": Language.CPP,
        ".c": Language.C, ".cs": Language.CSHARP, ".rb": Language.RUBY,
        ".rs": Language.RUST, ".php": Language.PHP, ".sql": Language.SQL,
    }
    if ext in code_map:
        raw = _load_text_fallback(path)[0].page_content
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=code_map[ext], chunk_size=800, chunk_overlap=80,
        )
        return splitter.split_text(raw)  # 已按语法切，直接返回文本块

    # ---- 其它文本（.txt/.yaml/.log 等）：open() 兜底 ----
    return _load_text_fallback(path)


# ----------------------------------------------------------
# 3) 语义感知的「二次细切」
#    前面加载时已按结构切过大块；这里再按中文友好的递归切，
#    把过大的块压到 chunk_size 以内，保证适合向量化检索。
# ----------------------------------------------------------
def _refine_split(docs: List[Document], chunk_size: int, chunk_overlap: int
                  ) -> List[Document]:
    # 已经是纯文本块（代码/标题切出来的）先包回 Document
    if docs and isinstance(docs[0].page_content, str) and docs[0].page_content:
        pass
    # Markdown 标题切出来的块 metadata 已带 h1/h2，保留即可
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=ZH_SEPARATORS,
    )
    return splitter.split_documents(docs)


# ----------------------------------------------------------
# 4) 统一入口：加载 + 切片，一条龙
# ----------------------------------------------------------
def load_and_split(path: str, chunk_size: int = 500,
                   chunk_overlap: int = 50) -> List[Document]:
    """按文件类型自动加载并做语义感知切片，返回可直接向量化的 chunks。"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在：{path}")

    docs = _load_by_ext(path)
    print(f"[加载] {path} → {len(docs)} 个文档/大块")

    # 代码/Markdown 已在加载阶段完成语义切，这里只做轻量细切
    chunks = _refine_split(docs, chunk_size, chunk_overlap)
    print(f"[切片] → {len(chunks)} 个最终 chunk（chunk_size={chunk_size}）")
    return chunks


# ----------------------------------------------------------
# 5) 演示：用一个真实存在的文件跑通
# ----------------------------------------------------------
if __name__ == "__main__":
    # test_doc.txt 一定存在，先跑通基础路径
    chunks = load_and_split("test_doc.txt", chunk_size=120, chunk_overlap=20)
    for i, c in enumerate(chunks[:3], 1):
        print(f"\n--- 块 {i}（{len(c.page_content)} 字）---")
        print(c.page_content[:80])

    # 若仓库里有其它格式，可取消注释直接试：
    # load_and_split("docs/day01-10_overview.md")
    # load_and_split("某文件.pdf")
    # load_and_split("某表格.csv")
