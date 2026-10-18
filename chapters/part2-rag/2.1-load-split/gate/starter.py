"""L2.1 文档加载与切分 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
load_split.py / load_split_formats.py。实现下面两个函数，然后运行：

    python chapters/part2-rag/2.1-load-split/gate/gate_check.py
"""

from __future__ import annotations

from pathlib import Path


def load_text(path: str | Path) -> dict:
    """读取 UTF-8 文本，返回 {"text": str, "source": 文件名}。

    要求：
    - 路径不存在/不是文件 -> ValueError；
    - 读取失败（编码等）-> ValueError；
    - source 只取文件名（Path.name），不暴露绝对路径。
    """
    raise NotImplementedError("实现文本加载")


def split_text(
    doc: dict,
    chunk_size: int = 120,
    overlap: int = 20,
) -> list[dict]:
    """把文档切成片段。

    返回 [{"text": str, "source": str, "index": int}, ...]。
    要求：
    - doc 必须是含 text/source 的 dict；空文本返回 []；
    - chunk_size <= 0、overlap < 0、overlap >= chunk_size -> ValueError；
    - 每个片段非空、长度不超过 chunk_size、index 从 1 连续编号；
    - source 原样复制到每个片段；
    - 相邻片段重叠 overlap 个字符（按字符切片）。
    """
    raise NotImplementedError("实现文档切分")
