"""Day77 运行与证据入口：服务能力和面试陈述引用同一份项目根目录。"""

import os
from pathlib import Path

from .api import create_app
from .auth import TokenVerifier
from .bootstrap import build_application
from .evidence import missing_evidence
from .feedback import FeedbackStore, attach_feedback_routes
from .settings import PROJECT_ROOT, Settings
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


def verify_project_evidence(paths: list[str]) -> None:
    missing = missing_evidence(PROJECT_ROOT, paths)
    if missing:
        raise RuntimeError("缺少项目证据：" + ", ".join(missing))
