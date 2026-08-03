"""启动前检查必须存在的资料与 provider 配置，失败时给出明确原因。"""

from .settings import Settings


def readiness(settings: Settings):
    errors = []
    if not settings.knowledge_path.exists():
        errors.append("knowledge_missing")
    if settings.llm_provider == "deepseek" and not settings.llm_api_key:
        errors.append("api_key_missing")
    return errors
