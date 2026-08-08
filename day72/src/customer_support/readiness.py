"""Day72 发布检查：静态启动条件与容量结果必须同时通过。"""

from .capacity import report
from .settings import Settings


def readiness(settings: Settings):
    errors = []
    if not settings.knowledge_path.exists():
        errors.append("knowledge_missing")
    if settings.llm_provider == "deepseek" and not settings.llm_api_key:
        errors.append("api_key_missing")
    return errors


def ensure_ready(settings: Settings) -> None:
    errors = readiness(settings)
    if errors:
        raise RuntimeError("readiness failed: " + ", ".join(errors))


def release_readiness(settings: Settings, latencies, statuses) -> list[str]:
    """部署门同时消费运行配置和压测证据。"""

    errors = readiness(settings)
    capacity = report(latencies, statuses)
    if not capacity.passed:
        errors.append(
            f"capacity_failed:p95={capacity.p95_ms},error_rate={capacity.error_rate}"
        )
    return errors
