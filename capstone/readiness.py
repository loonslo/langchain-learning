"""无模型费用的依赖 readiness；与仅表示进程存活的 `/live` 分离。"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from . import config as C
from .auth import auth_configuration_errors, get_rate_limiter
from .content_safety import configuration_errors as safety_configuration_errors
from .knowledge_base import SUPPORTED_SUFFIXES


def check() -> list[str]:
    errors = [
        *C.validate_settings(),
        *auth_configuration_errors(),
        *safety_configuration_errors(),
    ]
    try:
        C.ensure_runtime_directories()
        if not os.access(C.DATA_DIR, os.W_OK):
            errors.append(f"数据目录不可写：{C.DATA_DIR}")
    except OSError as exc:
        errors.append(f"数据目录不可用：{exc}")

    docs_available = C.DOCS_DIR.is_dir() and any(
        path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        for path in C.DOCS_DIR.rglob("*")
    )
    if not docs_available:
        errors.append(f"默认知识目录没有可用文档：{C.DOCS_DIR}")

    try:
        with sqlite3.connect(C.METRICS_DB_PATH, timeout=1) as connection:
            connection.execute("SELECT 1").fetchone()
    except sqlite3.Error as exc:
        errors.append(f"指标存储不可用：{exc}")

    if C.ENABLE_QUERY_TOOL and not Path(C.DB_PATH).is_file():
        errors.append(f"已启用受控查询但业务数据库不存在：{C.DB_PATH}")

    if os.getenv("REDIS_URL"):
        try:
            limiter = get_rate_limiter()
            client = getattr(limiter, "client", None)
            if client is None or not client.ping():
                errors.append("Redis 限流后端未响应")
        except Exception as exc:
            errors.append(f"Redis 限流后端不可用：{type(exc).__name__}")
    return errors
