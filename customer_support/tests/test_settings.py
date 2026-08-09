"""验证环境变量缺失、供应商切换和密钥优先级这三类配置场景。"""

from src.settings import Settings


CONFIG_NAMES = (
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "DEEPSEEK_API_KEY",
    "EMBED_DEVICE",
)


def clear_llm_environment(monkeypatch):
    """让每个测试从没有 LLM 配置的干净环境开始，避免相互影响。"""
    for name in CONFIG_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_defaults_to_local_ollama(monkeypatch):
    # 不设置任何变量时应能离线启动本机 Ollama，这是初学者的默认体验。
    clear_llm_environment(monkeypatch)

    settings = Settings.from_env()

    assert settings.llm_provider == "ollama"
    assert settings.llm_model == "qwen3.5:9b"
    assert settings.llm_base_url == "http://localhost:11434"
    assert settings.llm_api_key == ""
    assert settings.embedding_device == "cpu"


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
