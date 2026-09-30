"""启动前检查必须存在的资料与 provider 配置，失败时给出明确原因。"""

from .settings import Settings


def readiness(settings: Settings):
    """返回启动前发现的问题：知识库路径不存在、deepseek 缺 API Key；空列表表示就绪。"""
    errors = []
    if not settings.knowledge_path.exists():
        errors.append("knowledge_missing")
    if settings.llm_provider == "deepseek" and not settings.llm_api_key:
        errors.append("api_key_missing")
    return errors


def ensure_ready(settings: Settings) -> None:
    """供 CLI、API 和容器共同调用；不允许带着已知缺口启动。"""

    errors = readiness(settings)
    if errors:
        raise RuntimeError("readiness failed: " + ", ".join(errors))
