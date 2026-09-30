"""
章节 2.1 · 多种文件格式的加载与切分
==========================================================
load_split.py 只读 txt。本文件把常见格式统一成一个入口 load_and_split(path)：

1. 加载：按文件扩展名选加载器，统一产出 List[Document]
2. 切分：先按内容结构切（标题、语法、记录），再用中文递归切分器把过长的块压到 chunk_size 以内

按结构切分 = 在标题、函数、记录这类自然边界下刀，而不是按字符位置硬切：
  - .md          按标题层级切（MarkdownHeaderTextSplitter），标题写入 metadata
  - .py/.js/...  按语法切（RecursiveCharacterTextSplitter.from_language），不切断函数
  - .pdf         每页一个 Document（PyPDFLoader）
  - .docx        按段落/标题元素切（UnstructuredWordDocumentLoader，未安装则退回 docx2txt 读全文）
  - .csv/.json   一条记录 = 一个 Document
  - .txt 及其他  直接读全文；没有结构可利用，全靠后面的递归切分

依赖（requirements-course.txt 未列入的可选项按需安装）：
  已有：pypdf、langchain-community、langchain-text-splitters
  可选：.docx → pip install docx2txt（或 unstructured）；.html → pip install bs4

运行：python tools/run_chapter.py 2.1 load_split_formats.py
在别的脚本中使用：
  from load_split_formats import load_and_split
  chunks = load_and_split("手册.pdf")
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
    Language,
)

# 复用根目录 common.py 的公共配置（中文分隔符、示例文档路径）
try:
    from common import ZH_SEPARATORS, LONG_DOC
except Exception:  # 脱离本仓库单独运行本文件时的兜底
    ZH_SEPARATORS = ["\n\n", "\n", "。", "，", " ", ""]
    LONG_DOC = Path(__file__).resolve().parents[2] / "shared-data" / "long_article.txt"


# ----------------------------------------------------------
# 1) 兜底：读整个文本文件，包成一个 Document（与 load_split.py 的写法相同）
# ----------------------------------------------------------
def _load_text_fallback(path: str) -> List[Document]:
    with open(path, encoding="utf-8") as f:
        return [Document(page_content=f.read(), metadata={"source": path})]


# ----------------------------------------------------------
# 2) 按扩展名选择加载器
#    每个分支的目标相同：产出 List[Document]，并尽量在结构边界上切好
# ----------------------------------------------------------
def _load_by_ext(path: str) -> List[Document]:
    ext = Path(path).suffix.lower()

    # ---- .pdf：每页一个 Document（页是粗粒度的天然边界）----
    if ext == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader
        return PyPDFLoader(path).load()

    # ---- .docx：优先按段落/标题元素切；没装 unstructured 就退回读全文 ----
    if ext == ".docx":
        try:
            from langchain_community.document_loaders import (
                UnstructuredWordDocumentLoader,
            )
            return UnstructuredWordDocumentLoader(path, mode="elements").load()
        except Exception:
            try:
                import docx2txt
                text = docx2txt.process(path) or ""
                return [Document(page_content=text, metadata={"source": path})]
            except Exception:
                raise RuntimeError("读 .docx 需要 pip install unstructured 或 docx2txt")

    # ---- .csv：每行 = 一条记录 = 一个 Document ----
    if ext == ".csv":
        from langchain_community.document_loaders import CSVLoader
        return CSVLoader(path, encoding="utf-8").load()

    # ---- .json / .jsonl：数组的每个元素 = 一个 Document ----
    if ext in (".json", ".jsonl"):
        import json
        with open(path, encoding="utf-8") as f:
            if ext == ".jsonl":   # jsonl：每行一个 JSON 对象
                data = [json.loads(line) for line in f if line.strip()]
            else:
                data = json.load(f)
        if isinstance(data, list):
            return [
                Document(page_content=json.dumps(item, ensure_ascii=False),
                         metadata={"source": path, "index": i})
                for i, item in enumerate(data)
            ]
        return [Document(page_content=json.dumps(data, ensure_ascii=False),
                         metadata={"source": path})]

    # ---- .md：按 # / ## / ### 标题层级切，标题写进 metadata ----
    if ext == ".md":
        raw = _load_text_fallback(path)[0].page_content
        md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
            ("#", "h1"), ("##", "h2"), ("###", "h3"),
        ])
        docs = md_splitter.split_text(raw)
        for d in docs:                      # 标题切分器不带来源，补上
            d.metadata["source"] = path
        return docs

    # ---- .html / .htm：优先按元素切，退回 BeautifulSoup 提取正文 ----
    if ext in (".html", ".htm"):
        try:
            from langchain_community.document_loaders import (
                UnstructuredHTMLLoader,
            )
            return UnstructuredHTMLLoader(path, mode="elements").load()
        except Exception:
            from langchain_community.document_loaders import BS4HTMLLoader
            return BS4HTMLLoader(path).load()   # 需要 pip install bs4

    # ---- 代码：按扩展名映射到 Language，按语法结构切 ----
    code_map = {
        ".py": Language.PYTHON, ".js": Language.JS, ".ts": Language.TS,
        ".java": Language.JAVA, ".go": Language.GO, ".cpp": Language.CPP,
        ".c": Language.C, ".cs": Language.CSHARP, ".rb": Language.RUBY,
        ".rs": Language.RUST, ".php": Language.PHP,
    }  # langchain-text-splitters 没有 SQL 语法切分，.sql 走下面的纯文本兜底
    if ext in code_map:
        raw = _load_text_fallback(path)[0].page_content
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=code_map[ext], chunk_size=800, chunk_overlap=80,
        )
        # create_documents 把文本块包成 Document，并带上来源
        return splitter.create_documents([raw], metadatas=[{"source": path}])

    # ---- 其他文本（.txt / .yaml / .log 等）：读全文 ----
    return _load_text_fallback(path)


# ----------------------------------------------------------
# 3) 二次切分：把前面按结构切出来的大块，压到 chunk_size 以内
#    metadata（来源、页码、标题）会随块保留
# ----------------------------------------------------------
def _refine_split(docs: List[Document], chunk_size: int, chunk_overlap: int
                  ) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=ZH_SEPARATORS,
    )
    return splitter.split_documents(docs)


# ----------------------------------------------------------
# 4) 统一入口：加载 + 切分
# ----------------------------------------------------------
def load_and_split(path: str, chunk_size: int = 500,
                   chunk_overlap: int = 50) -> List[Document]:
    """按文件类型加载并切分，返回可直接向量化的 chunks。"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在：{path}")

    docs = _load_by_ext(path)
    print(f"[加载] {path} → {len(docs)} 个文档/大块")

    chunks = _refine_split(docs, chunk_size, chunk_overlap)
    print(f"[切分] → {len(chunks)} 个 chunk（chunk_size={chunk_size}）")
    return chunks


# ----------------------------------------------------------
# 5) 演示：先切长文章（txt，无结构），再切本章 README（md，按标题结构）
# ----------------------------------------------------------
if __name__ == "__main__":
    chunks = load_and_split(str(LONG_DOC), chunk_size=120, chunk_overlap=20)
    for i, c in enumerate(chunks[:3], 1):
        print(f"\n--- 块 {i}（{len(c.page_content)} 字）---")
        print(c.page_content[:80])

    # Markdown：每个块的 metadata 里带有它所属的标题
    md_chunks = load_and_split(str(Path(__file__).with_name("README.md")), chunk_size=300)
    print("\n第一个 Markdown 块的 metadata：", md_chunks[0].metadata)

    # 其他格式同理，换成自己的文件即可：
    # load_and_split("某文件.pdf")
    # load_and_split("某表格.csv")
