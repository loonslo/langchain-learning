"""启动前检查：课程环境不能把显然不安全的默认值伪装成可部署。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeSettings:
    database_url: str
    redis_url: str
    qdrant_url: str
    app_env: str = "development"


def configuration_errors(settings: RuntimeSettings) -> tuple[str, ...]:
    """返回启动前的配置错误（空元组表示通过）：三个 URL 的协议是否正确；生产环境不得使用示例数据库密码（含 change-me）。
    只做这两类检查，不验证服务是否可连通。
    """
    errors: list[str] = []
    if not settings.database_url.startswith("postgresql://"):
        errors.append("DATABASE_URL 必须是 postgresql:// URL")
    if not settings.redis_url.startswith("redis://"):
        errors.append("REDIS_URL 必须是 redis:// URL")
    if not settings.qdrant_url.startswith(("http://", "https://")):
        errors.append("QDRANT_URL 必须是 HTTP URL")
    if settings.app_env == "production" and "change-me" in settings.database_url:
        errors.append("生产环境禁止使用示例数据库密码")
    return tuple(errors)
