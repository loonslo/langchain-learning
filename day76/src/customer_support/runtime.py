"""Day76 最终组合入口：所有已学能力进入同一个 FastAPI 进程。"""

import os
from pathlib import Path

from .api import create_app
from .auth import TokenVerifier
from .bootstrap import build_application
from .feedback import FeedbackStore, attach_feedback_routes
from .settings import Settings
from .sync import SyncingApplication
from .thread_store import SQLiteThreadStore


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


def backup_threads(target: Path, settings: Settings | None = None) -> Path:
    settings = settings or Settings.from_env()
    return SQLiteThreadStore(settings.thread_db_path).backup_to(target)
