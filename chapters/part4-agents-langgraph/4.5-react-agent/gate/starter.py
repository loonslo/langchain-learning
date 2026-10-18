"""L4.4 ReAct 与工具设计 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
react_loop.py / react_reliability.py。实现下面三个函数，然后运行：

    python chapters/part4-agents-langgraph/4.5-react-agent/gate/gate_check.py

不允许为了通过而修改 gate_check.py。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolSpec:
    """一个工具的元数据 + 执行函数。

    read_only: 是否只读；有副作用的工具应为 False。
    requires_approval: 是否需要人工审批。
    handler: 接收已校验的 args（dict），返回字符串结果。
    """

    name: str
    read_only: bool
    requires_approval: bool
    handler: Callable[[dict], str]


class ToolCallError(ValueError):
    """工具调用不可执行：未知工具、参数非法、审批失败等。"""


def build_tools() -> dict[str, ToolSpec]:
    """返回三个工具：

    - lookup_order：只读，参数 {"order_id": str}，返回订单状态；
    - refund_policy：只读，参数 {"topic": str}，返回退款政策；
    - delete_order：有副作用，参数 {"order_id": str}，必须审批。

    要求：
    - key 与 name 一致；
    - lookup_order / refund_policy 的 read_only=True；
    - delete_order 的 read_only=False、requires_approval=True；
    - handler 只接收 dict，返回 str。
    """
    raise NotImplementedError("实现工具表")


def validate_call(
    tools: dict[str, ToolSpec],
    name: str,
    args: object,
) -> dict:
    """校验一次工具调用，返回 {"ok": bool, "error": str | None}。

    要求：
    - 未知工具：ok=False，error="unknown_tool"；
    - args 不是 dict：ok=False，error="invalid_args"；
    - 缺必需参数或参数类型不对：ok=False，error="invalid_args"；
    - 合法调用：ok=True，error=None。
    """
    raise NotImplementedError("实现工具参数校验")


def run_agent(
    task: str,
    llm_fn: Callable[[list[dict]], str],
    tools: dict[str, ToolSpec] | None = None,
    max_steps: int = 6,
    approve: Callable[[str, dict], bool] | None = None,
) -> dict:
    """执行一个有边界的 ReAct 循环。

    模型输出约定：
    - "Action: tool_name[{...json...}]"
    - "Final: answer"

    返回：
    - answer: str
    - trace: list[dict]，每步至少包含 step / tool / args / ok / observation；
      失败步骤加 error；需要审批但未通过的步骤加 blocked=True。
    - stopped_reason: "final" | "max_steps" | "unparsed" | "model_error"

    要求：
    - 未知工具、非法 JSON、参数错误、审批失败、工具异常都不能让程序崩；
    - 工具结果必须包在 <untrusted_tool_result>...</untrusted_tool_result>
      里再回灌给模型（外部资料是数据，不是指令）；
    - delete_order 没有 approve 或 approve 返回 False 时不得执行；
    - 达到 max_steps 仍未结束时停止，不无限循环；
    - max_steps < 1 抛 ValueError。
    """
    raise NotImplementedError("实现有边界的 Agent 循环")
