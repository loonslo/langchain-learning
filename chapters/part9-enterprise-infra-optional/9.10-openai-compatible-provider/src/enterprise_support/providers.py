"""OpenAI 兼容模型服务的配置边界。"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class OpenAICompatibleProvider:
    """模型服务端点配置：base_url 以 /v1 结束；api_key_env 是环境变量名，密钥值不出现在配置里。"""

    name: str
    base_url: str
    model: str
    api_key_env: str
    app_env: str = "development"

    @property
    def chat_completions_url(self) -> str:
        """拼出 chat/completions 的完整地址（自动去掉 base_url 末尾的 /）。"""
        return self.base_url.rstrip("/") + "/chat/completions"


def validate_provider(provider: OpenAICompatibleProvider) -> tuple[str, ...]:
    """返回配置错误列表（空元组表示通过）；只校验形状，不发请求。"""
    errors: list[str] = []
    parsed = urlparse(provider.base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors.append("模型服务 base_url 必须是完整 HTTP(S) URL")
    if not parsed.path.rstrip("/").endswith("/v1"):
        errors.append("OpenAI 兼容服务 base_url 必须以 /v1 结束")
    if not provider.model.strip():
        errors.append("必须配置 model")
    if not provider.api_key_env or "=" in provider.api_key_env:
        errors.append("api_key_env 必须是环境变量名，不能写入密钥值")
    if provider.app_env == "production" and parsed.scheme != "https":
        errors.append("生产环境模型服务必须经 HTTPS 或受验证的内部 mTLS 代理访问")
    return tuple(errors)
