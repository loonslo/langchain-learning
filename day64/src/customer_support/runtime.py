"""Day64 运行入口：知识同步与问答共享同一份 Settings.knowledge_path。"""

import os

from .api import create_app
from .auth import TokenVerifier
from .bootstrap import build_application
from .settings import Settings
from .sync import SyncingApplication


def create_runtime_api():
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET 至少需要 32 个字符")
    settings = Settings.from_env()
    service = SyncingApplication(build_application(settings), settings.knowledge_path)
    return create_app(service, TokenVerifier(secret))
