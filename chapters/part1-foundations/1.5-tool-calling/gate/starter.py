"""L1.5 工具调用 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
tool_calling.py。实现下面三个部分，然后运行：

    python chapters/part1-foundations/1.5-tool-calling/gate/gate_check.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, type]
    handler: Callable[[dict], str]


class ToolError(ValueError):
    """工具调用不合法。"""


def build_tools() -> dict[str, ToolSpec]:
    """返回两个工具：

    - get_weather：参数 {"city": str}，返回天气；
    - calculate：参数 {"expression": str}，返回计算结果。

    要求：key 与 name 一致；description 非空；handler 只接收 dict，返回 str。
    """
    raise NotImplementedError("实现工具表")


def dispatch_tool(
    tools: dict[str, ToolSpec],
    name: str,
    args: object,
) -> dict:
    """执行一次工具调用。

    返回 {"ok": bool, "result": str, "error": str | None}。
    要求：
    - 未知工具 -> error="unknown_tool"；
    - args 不是 dict -> error="invalid_args"；
    - 缺参数/类型错 -> error="invalid_args"；
    - handler 抛异常 -> error="tool_error"；
    - handler 返回非 str -> error="invalid_tool_output"。
    """
    raise NotImplementedError("实现工具分发")


def run_tool_loop(
    messages: list[dict],
    llm_fn: Callable[[list[dict]], dict],
    tools: dict[str, ToolSpec] | None = None,
    max_steps: int = 3,
) -> dict:
    """执行“模型请求工具 → 程序执行 → 结果喂回”的循环。

    llm_fn 返回：
        {"content": str, "tool_calls": [{"id": str, "name": str, "args": dict}]}

    返回：
    - answer: str
    - trace: list[dict]（每步 tool/args/ok/result/error）
    - stopped_reason: "final" | "max_steps" | "model_error"

    要求：
    - 没有 tool_calls 时直接返回 content，stopped_reason="final"；
    - 每个工具结果都要以 role="tool" 的消息追加回 messages，带上 tool_call_id；
    - 未知工具/参数错误/工具异常不崩，记录到 trace，继续；
    - max_steps < 1 抛 ValueError；
    - llm_fn 超时/异常 -> stopped_reason="model_error"。
    """
    raise NotImplementedError("实现工具循环")
