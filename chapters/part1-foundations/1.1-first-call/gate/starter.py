"""L1.1 一次调用 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
first_call.py。实现下面三个函数，然后运行：

    python chapters/part1-foundations/1.1-first-call/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable


class CallError(RuntimeError):
    """可预期的调用/解析失败。"""


def build_messages(system: str, question: str) -> list[dict]:
    """构造一次调用的消息列表。

    要求：
    - 返回 [{"role": "system", "content": system}, {"role": "user", "content": question}]；
    - system 或 question 为空字符串时抛 ValueError；
    - 不修改传入参数。
    """
    raise NotImplementedError("实现消息构造")


def parse_response(response: object) -> dict:
    """把模型返回对象压成程序可用的字段。

    返回：
    - content: str
    - input_tokens: int
    - output_tokens: int
    - finish_reason: str（缺省 "stop"）

    要求：
    - response 必须是 dict，否则抛 CallError("bad_response")；
    - content 缺失/不是字符串/为空，抛 CallError("empty_response")；
    - usage 缺失时 token 记 0；usage 里的字段不是 int 时记 0。
    """
    raise NotImplementedError("实现响应解析")


def call_once(
    system: str,
    question: str,
    chat_fn: Callable[[list[dict]], object],
) -> dict:
    """执行一次调用并把失败转成可读结果。

    chat_fn(messages) 返回模型对象（通常含 content/usage）。
    返回：
    - content: str
    - input_tokens: int
    - output_tokens: int
    - finish_reason: str
    - error: str | None（timeout / model_error / empty_response / bad_response）

    要求：
    - question 为空时抛 ValueError；
    - chat_fn 超时 -> error="timeout"，content=""；
    - chat_fn 其他异常 -> error="model_error"，content=""；
    - 解析失败按 parse_response 的错误返回，不把异常抛给调用方。
    """
    raise NotImplementedError("实现一次调用")
