"""L1.6 手写 Harness · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
raw_sdk_rag_agent_loop.py。实现下面四个函数，然后运行：

    python chapters/part2-rag/2.5-raw-sdk-rag-agent-loop/gate/gate_check.py

不允许为了通过而修改 gate_check.py。可以查 Python 标准库文档。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Chunk:
    """一个可追溯的文本片段；source + index 组成引用标识。"""

    text: str
    source: str
    index: int


class HarnessError(Exception):
    """可预期的 harness 失败；gate 要求把它转成可读结果，而不是未处理异常。"""


def split_text(
    text: str,
    source: str,
    chunk_size: int = 180,
    overlap: int = 30,
) -> list[Chunk]:
    """把 text 切成片段。

    要求：
    - 空文本返回 []；
    - chunk_size <= 0 或 overlap < 0 或 overlap >= chunk_size 时抛 ValueError；
    - 每个片段非空，source 原样保留，index 从 1 开始；
    - 每个片段的长度不超过 chunk_size（按 Python 字符数，不按字节）。
    """
    raise NotImplementedError("实现切分")


def retrieve(query: str, chunks: list[Chunk], k: int = 3) -> list[Chunk]:
    """返回与 query 相关的片段，最多 k 个。

    要求：
    - 只返回分数 > 0 的片段，按分数降序；
    - query 为空或 chunks 为空时返回 []；
    - 不修改传入的 chunks。
    """
    raise NotImplementedError("实现检索")


def answer(
    question: str,
    chunks: list[Chunk],
    chat_fn: Callable[[list[dict]], str],
) -> dict:
    """基于检索结果回答，并返回可追溯的来源。

    返回字段：
    - answer: str
    - sources: list[str]，格式为 "source#index"
    - refused: bool
    - error: str | None，可读的失败原因

    要求：
    - 空问题或没有命中片段：refused=True，sources=[]，不调用 chat_fn；
    - 有命中：调用 chat_fn(messages)，sources 按检索顺序；
    - chat_fn 超时/抛异常/返回空串：不把异常抛给调用方，返回 refused=True
      和可读的 error（timeout / model_error / empty_response）。
    """
    raise NotImplementedError("实现 RAG 回答")


def run_agent(
    task: str,
    chat_fn: Callable[[list[dict]], str],
    tools: dict[str, Callable[[str], str]],
    max_steps: int = 4,
) -> dict:
    """执行一个最小 ReAct 循环。

    模型输出约定：
    - "Action: tool_name[argument]" 表示请求工具；
    - "Final: answer" 表示结束。

    返回字段：
    - answer: str
    - trace: list[dict]，每步至少包含 step / tool / arg / ok / observation；
    - stopped_reason: "final" | "max_steps" | "unparsed" | "model_error"

    要求：
    - 未知工具、工具抛异常都不能让程序崩；trace 里记录 ok=False 和 error；
    - 解析不到 Action/Final 时，把模型原文当 answer，stopped_reason="unparsed"；
    - 达到 max_steps 仍未结束时，answer 给出可读提示，stopped_reason="max_steps"；
    - chat_fn 超时/抛异常时，不把异常抛给调用方，stopped_reason="model_error"。
    """
    raise NotImplementedError("实现 Agent 循环")
