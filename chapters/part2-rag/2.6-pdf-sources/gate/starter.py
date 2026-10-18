"""L2.3 扩展 · PDF 与来源溯源 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
pdf_sources.py。实现下面三个函数，然后运行：

    python chapters/part2-rag/2.6-pdf-sources/gate/gate_check.py
"""

from __future__ import annotations


def load_pages(pages: list[tuple[int, str]], source: str) -> list[dict]:
    """把 (页码, 文本) 转成带来源的片段。

    返回 [{"text": str, "source": str, "page": int}, ...]。
    要求：
    - source 非空；页码是 >=1 的整数，否则 ValueError；
    - 空白页跳过；
    - 保持输入顺序。
    """
    raise NotImplementedError("实现按页加载")


def format_context(docs: list[dict]) -> str:
    """把片段拼成带页码的上下文。

    每段格式：
    - 有 page：`[来源：file 第2页]\\n正文`
    - 无 page：`[来源：file]\\n正文`
    段间用两个换行分隔；空列表返回 ""；片段缺字段/类型错 -> ValueError。
    """
    raise NotImplementedError("实现带来源的上下文")


def verify_citations(answer: str, docs: list[dict]) -> dict:
    """核对答案里的【来源：...】标记是否都能在 docs 中找到。

    返回：
    - ok: bool（至少有一个引用，且没有未知引用）
    - cited: list[str]（规范化后的引用，按出现顺序去重）
    - unknown: list[str]（docs 中不存在的引用）

    规范化：有 page 用 "source#p页码"，无 page 用 "source"。
    要求：
    - answer 不是字符串 -> ValueError；
    - docs 缺字段/类型错 -> ValueError。
    """
    raise NotImplementedError("实现引用核对")
