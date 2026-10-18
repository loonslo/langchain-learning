"""L2.4 切分策略 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
chunk_strategy.py。实现下面两个函数，然后运行：

    python chapters/part2-rag/2.7-chunk-strategy/gate/gate_check.py
"""

from __future__ import annotations


def split_preserving_boundaries(text: str, max_chars: int) -> list[str]:
    """优先按段落、再按句子、最后硬切，保证每段不超过 max_chars。

    要求：
    - 空文本返回 []；max_chars <= 0 -> ValueError；
    - 先按空行分段；段落放得下就整段保留；
    - 段落超长时按中文/英文句末标点（。！？!?）切句；
    - 单句仍超长时才硬切；
    - 不产生空片段；输出顺序与原文一致。
    """
    raise NotImplementedError("实现保边界切分")


def chunk_stats(chunks: list[str]) -> dict:
    """返回 {"count","avg_len","max_len","empty_count"}。

    要求：空列表时 avg_len/max_len 为 0；empty_count 统计空片段。
    """
    raise NotImplementedError("实现切分统计")
