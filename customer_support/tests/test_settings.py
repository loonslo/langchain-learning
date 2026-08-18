"""验证 DeepSeek 默认配置、供应商限制和密钥优先级。"""

import pytest

from src.settings import Settings


CONFIG_NAMES = (
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "DEEPSEEK_API_KEY",
    "EMBED_MODEL_PATH",
    "EMBED_DEVICE",
)


def clear_llm_environment(monkeypatch):
    """让每个测试从没有 LLM 配置的干净环境开始，避免相互影响。"""
    for name in CONFIG_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_defaults_to_deepseek(monkeypatch):
    # 不设置 provider 时默认使用 DeepSeek，避免启动时误连本机 Ollama。
    clear_llm_environment(monkeypatch)

    settings = Settings.from_env()

    assert settings.llm_provider == "deepseek"
    assert settings.llm_model == "deepseek-chat"
    assert settings.llm_base_url == "https://api.deepseek.com"
    assert settings.llm_api_key == ""
    assert settings.embedding_model == "BAAI/bge-small-zh-v1.5"
    assert settings.embedding_device == "cpu"


def test_non_deepseek_provider_is_rejected(monkeypatch):
    # 明确拒绝旧 Ollama 配置，避免用户以为项目仍支持本地聊天模型。
    clear_llm_environment(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")

    with pytest.raises(ValueError, match="仅支持 DeepSeek"):
        Settings.from_env()


def test_deepseek_uses_provider_defaults_and_existing_key_name(monkeypatch):
    # 兼容旧的 DEEPSEEK_API_KEY 名称，降低已有 .env 文件的迁移成本。
    clear_llm_environment(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    settings = Settings.from_env()

    assert settings.llm_model == "deepseek-chat"
    assert settings.llm_base_url == "https://api.deepseek.com"
    assert settings.llm_api_key == "test-key"


def test_explicit_llm_key_takes_precedence(monkeypatch):
    # 新的通用变量 LLM_API_KEY 优先，避免多个密钥同时存在时含义不明确。
    clear_llm_environment(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_API_KEY", "primary-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fallback-key")
    monkeypatch.setenv("EMBED_DEVICE", "CUDA")

    settings = Settings.from_env()

    assert settings.llm_api_key == "primary-key"
    assert settings.embedding_device == "cuda"
