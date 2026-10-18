"""L1.7 CLI 助手 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
chatbot_project.py。实现下面这个函数，然后运行：

    python chapters/part1-foundations/1.8-cli-chatbot/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable, Iterable

SYSTEM_PROMPT = "你是一个命令行助手，用简洁中文回答。"


class CLIError(ValueError):
    """CLI 参数或输入不合法。"""


def run_cli(
    inputs: Iterable[str],
    chat_fn: Callable[[list[dict]], dict],
    tools: dict[str, Callable[[dict], str]] | None = None,
    max_turns: int = 20,
) -> dict:
    """执行脚本化的 CLI 循环。

    chat_fn(messages) 返回：
        {"content": str, "tool_calls": [{"id": str, "name": str, "args": dict}]}

    返回：
    - outputs: list[str]（每轮输出/系统提示）
    - trace: list[dict]（每轮 turn/input/output/tools）
    - exit_code: int（0 正常退出，1 模型/工具错误，2 达到 max_turns）
    - history: list[dict]（最终消息历史）

    要求：
    - 历史从 `{"role":"system","content":SYSTEM_PROMPT}` 开始；
    - 空行/纯空白忽略；
    - `clear` 清空历史（保留 system），输出“记忆已清除”；
    - `quit` 停止，exit_code=0，后续输入不再处理；
    - 正常输入：追加 user，调用 chat_fn；有 tool_calls 时执行工具、把
      role="tool" 结果回灌、再次调用 chat_fn；最终追加 assistant；
    - 未知工具/工具异常/模型异常 -> 输出可读错误，exit_code=1，停止；
    - 超过 max_turns -> exit_code=2，停止；
    - max_turns < 1 -> CLIError。
    """
    raise NotImplementedError("实现 CLI 循环")
