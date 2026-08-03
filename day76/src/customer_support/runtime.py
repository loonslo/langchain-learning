"""生产组合入口：创建真实 RAG，再接缓存、订单、工单、身份与 FastAPI。"""

from __future__ import annotations
import os
from time import monotonic
from .api import create_app
from .application import SupportApplication
from .auth import TokenVerifier
from .bootstrap import build_assistant
from .cache import AnswerCache
from .orders import OrderRepository
from .tickets import TicketStore


def create_runtime_api():
    """供 ``uvicorn customer_support.runtime:create_runtime_api --factory`` 调用。"""
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET 至少需要 32 个字符")
    service = SupportApplication(
        build_assistant(),
        OrderRepository([]),
        TicketStore(),
        AnswerCache(ttl=60, clock=monotonic),
    )
    return create_app(service, TokenVerifier(secret))
