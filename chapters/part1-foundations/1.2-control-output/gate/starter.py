"""L1.2 输出控制 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
control_output.py。实现下面三个函数，然后运行：

    python chapters/part1-foundations/1.2-control-output/gate/gate_check.py
"""

import time
from typing import Callable, Iterable


class RequestError(ValueError):
    """请求参数不合法。"""


def build_request(
    temperature: float = 0.0,
    max_tokens: int = 512,
    stop: list[str] | None = None,
) -> dict:
    """构造请求参数。

    要求：
    - temperature 必须在 0–2（含端点）；
    - max_tokens 必须是 1–8192 的整数；
    - stop 缺省为 []；必须是 list，元素为非空字符串，最多 4 个；
    - 任何不合法抛 RequestError；
    - 返回 {"temperature": float, "max_tokens": int, "stop": list[str]}。
    """
    raise NotImplementedError("实现请求参数构造")


def collect_stream(
    chunks: Iterable[str],
    clock: Callable[[], float] = time.perf_counter,
) -> dict:
    """收集流式片段。

    返回：
    - text: str（按顺序拼接）
    - chunks: int（收到的片段数）
    - first_chunk_ms: int（从开始到第一个片段的毫秒数；没有片段为 -1）
    - error: str | None（empty_stream / bad_chunk / model_error）

    要求：
    - 空流 -> error="empty_stream"，text=""，chunks=0；
    - 片段不是 str -> error="bad_chunk"，保留此前已拼接的 text；
    - 迭代抛异常 -> error="model_error"；
    - 正常结束 -> error=None。
    """
    raise NotImplementedError("实现流式收集")


def stream_text(
    chat_fn: Callable[[dict], Iterable[str]],
    request: dict,
) -> dict:
    """把请求交给 chat_fn，收集它返回的流。

    要求：
    - chat_fn(request) 必须只调用一次，request 原样传入；
    - chat_fn 超时 -> error="timeout"；
    - chat_fn 其他异常 -> error="model_error"；
    - 正常时返回 collect_stream 的结果，error=None。
    """
    raise NotImplementedError("实现流式调用")
