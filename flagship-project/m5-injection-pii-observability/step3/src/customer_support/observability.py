"""记录操作、状态和延迟；trace 不保存原始客服问题。"""

from dataclasses import dataclass
from time import perf_counter


@dataclass(frozen=True)
class Trace:
    """一次操作的记录：操作名、租户、状态和耗时；不含问题原文。"""

    operation: str
    tenant: str
    status: str
    latency_ms: float


class Recorder:
    def __init__(self):
        self.records = []

    def measure(self, operation, tenant, function):
        """执行 function 并记录耗时和状态；异常照常抛出，同时记为 error。"""
        start = perf_counter()
        status = "ok"
        try:
            return function()
        except Exception:
            status = "error"
            raise
        finally:
            self.records.append(
                Trace(operation, tenant, status, (perf_counter() - start) * 1000)
            )


class ObservedApplication:
    """让正式产品的成功和异常都经过同一个不含原问题的计时边界。"""

    def __init__(self, application, recorder: Recorder):
        self.application = application
        self.recorder = recorder

    def handle(self, question, **kwargs):
        tenant = kwargs.get("tenant_id", "local")
        return self.recorder.measure(
            "support.handle",
            tenant,
            lambda: self.application.handle(question, **kwargs),
        )

    def ask(self, question, **kwargs):
        return self.handle(question, **kwargs).answer

    def __getattr__(self, name):
        return getattr(self.application, name)
