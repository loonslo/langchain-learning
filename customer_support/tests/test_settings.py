from customer_support.settings import Settings


CONFIG_NAMES = (
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "DEEPSEEK_API_KEY",
    "EMBED_DEVICE",
)


def clear_llm_environment(monkeypatch):
    for name in CONFIG_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_defaults_to_local_ollama(monkeypatch):
    clear_llm_environment(monkeypatch)

    settings = Settings.from_env()

    assert settings.llm_provider == "ollama"
    assert settings.llm_model == "qwen3.5:9b"
    assert settings.llm_base_url == "http://localhost:11434"
    assert settings.llm_api_key == ""
    assert settings.embedding_device == "cpu"


def test_deepseek_uses_provider_defaults_and_existing_key_name(monkeypatch):
    clear_llm_environment(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    settings = Settings.from_env()

    assert settings.llm_model == "deepseek-chat"
    assert settings.llm_base_url == "https://api.deepseek.com"
    assert settings.llm_api_key == "test-key"


def test_explicit_llm_key_takes_precedence(monkeypatch):
    clear_llm_environment(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_API_KEY", "primary-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fallback-key")
    monkeypatch.setenv("EMBED_DEVICE", "CUDA")

    settings = Settings.from_env()

    assert settings.llm_api_key == "primary-key"
    assert settings.embedding_device == "cuda"
