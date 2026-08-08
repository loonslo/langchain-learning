"""Day63 HTTP 组合入口：没有足够强的 JWT_SECRET 就拒绝启动。"""

import os

from .api import create_app
from .auth import TokenVerifier
from .bootstrap import build_application


def create_runtime_api():
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET 至少需要 32 个字符")
    return create_app(build_application(), TokenVerifier(secret))
