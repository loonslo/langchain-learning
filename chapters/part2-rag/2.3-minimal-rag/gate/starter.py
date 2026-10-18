"""L2.3 最小 RAG · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
minimal_rag.py。实现下面两个函数，然后运行：

    python chapters/part2-rag/2.3-minimal-rag/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable


def format_context(docs: list[dict], max_chars: int | None = None) -> str:
    """把检索片段拼成带来源标记的上下文。

    每个片段形如 {"text": str, "source": str}。
    要求：
    - 空列表 -> ""；
    - 每段前加 "[source]\\n"；
    - max_chars 不是 None 时，只放得下的片段才加入，按原顺序；
    - max_chars < 0 -> ValueError；片段缺字段/类型错 -> ValueError。
    """
    raise NotImplementedError("实现上下文拼接")


def answer_with_rag(
    question: str,
    retrieve_fn: Callable[[str], list[dict]],
    chat_fn: Callable[[list[dict]], str],
    max_context_chars: int = 1000,
) -> dict:
    """最小 RAG：检索 → 拼上下文 → 生成 → 引用/拒答。

    返回：
    - answer: str
    - sources: list[str]（去重，按出现顺序）
    - refused: bool
    - error: str | None（empty_question / retrieval_error / timeout / model_error / empty_response）

    要求：
    - question 为空 -> ValueError；
    - 没有检索结果 -> refused=True，answer="文档中没有提到。"，不调用 chat_fn；
    - 有结果 -> 调 chat_fn，sources 来自实际进入上下文的片段；
    - 检索/模型异常/空回答 -> refused=True 且 error 可读，不抛未处理异常。
    """
    raise NotImplementedError("实现最小 RAG")
