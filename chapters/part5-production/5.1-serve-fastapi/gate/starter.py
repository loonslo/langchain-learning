"""L5.1 FastAPI 服务与可靠性 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
serve_fastapi.py。实现下面三个函数，然后运行：

    python chapters/part5-production/5.1-serve-fastapi/gate/gate_check.py

不允许为了通过而修改 gate_check.py。
"""

from typing import Any, Callable

from fastapi import FastAPI


class UpstreamError(RuntimeError):
    """模型/检索上游不可用；调用方应把它转成 502。"""


class MemoryStore:
    """最小内存存储，只用于本地跑通；真实持久化见 5.4。"""

    def __init__(self) -> None:
        self.qa: list[dict] = []
        self.feedback: list[dict] = []

    def save_qa(self, **kwargs: Any) -> int:
        self.qa.append(kwargs)
        return len(self.qa)

    def save_feedback(
        self,
        conversation_id: int,
        rating: int,
        comment: str | None = None,
    ) -> int:
        if conversation_id < 1:
            raise ValueError("对话不存在")
        self.feedback.append(
            {"conversation_id": conversation_id, "rating": rating, "comment": comment}
        )
        return len(self.feedback)

    def daily_stats(self, days: int) -> list[dict]:
        return []

    def get_history(
        self,
        user_id: str,
        limit: int = 20,
        before_id: int | None = None,
    ) -> list[dict]:
        return []


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """按环境变量单价估算成本（美元）。

    单价：PRICE_IN_PER_M / PRICE_OUT_PER_M，单位美元/百万 token。
    要求：每次调用时读取环境变量；token 为负数时按 0 处理。
    """
    raise NotImplementedError("实现成本估算")


def call_with_retry(
    fn: Callable[[], Any],
    attempts: int = 2,
    timeout_s: float | None = 5.0,
) -> Any:
    """调用 fn，带超时与有限重试。

    要求：
    - attempts < 1 抛 ValueError；
    - 只重试 TimeoutError / ConnectionError / UpstreamError；
    - 其他异常立即抛出，不重试；
    - 每次尝试超过 timeout_s 视为 TimeoutError；
    - 重试耗尽抛 UpstreamError，错误信息包含最后一次原因；
    - timeout_s=None 表示不限制。
    """
    raise NotImplementedError("实现超时与重试")


def create_app(
    answer_fn: Callable[[str], dict] | None = None,
    store: Any | None = None,
) -> FastAPI:
    """构造服务。

    answer_fn(question) 返回：
        {"answer": str, "sources": list[str],
         "prompt_tokens": int, "completion_tokens": int}

    store 需要提供：
        save_qa(**kwargs) -> int
        save_feedback(conversation_id, rating, comment=None) -> int
        daily_stats(days) -> list[dict]
        get_history(user_id, limit, before_id) -> list[dict]

    要求：
    - /health 永远 200；/ready 在 answer_fn 为 None 时 503；
    - /chat 校验 question 长度 1–1000；返回 answer/sources/conversation_id/
      trace_id/latency_ms；响应头 X-Trace-Id 与 body 一致；
    - answer_fn 为空时 /chat 503；
    - 上游 TimeoutError/ConnectionError/UpstreamError -> 502，body 含 trace_id；
    - 其他未处理异常 -> 500，body 含 trace_id，不泄露堆栈；
    - 成功和失败都调用 store.save_qa，失败时 status="error"；
    - /feedback 的 rating 只允许 1 或 -1，否则 422；
    - /stats、/history 直接读 store。
    """
    raise NotImplementedError("实现 FastAPI 服务")
