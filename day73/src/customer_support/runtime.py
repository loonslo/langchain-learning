"""Day73 运行入口：问答、同步计划和反馈共用一个 FastAPI 应用。"""

import os

from .api import create_app
from .auth import TokenVerifier
from .bootstrap import build_application
from .feedback import FeedbackStore, attach_feedback_routes
from .settings import Settings
from .sync import SyncingApplication


def create_runtime_api():
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET 至少需要 32 个字符")
    settings = Settings.from_env()
    verifier = TokenVerifier(secret)
    service = SyncingApplication(build_application(settings), settings.knowledge_path)
    app = create_app(service, verifier)
    attach_feedback_routes(app, FeedbackStore(), verifier)
    return app
