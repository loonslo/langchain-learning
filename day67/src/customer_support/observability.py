"""记录操作、状态和延迟；trace 不保存原始客服问题。"""

from dataclasses import dataclass
from time import perf_counter


@dataclass(frozen=True)
class Trace:
    operation: str
    tenant: str
    status: str
    latency_ms: float


class Recorder:
    def __init__(self):
        self.records = []

    def measure(self, operation, tenant, function):
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
