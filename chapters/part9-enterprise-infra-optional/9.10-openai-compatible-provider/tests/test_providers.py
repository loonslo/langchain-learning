from src.enterprise_support.providers import OpenAICompatibleProvider, validate_provider


def test_vllm_can_use_the_same_openai_compatible_contract():
    provider = OpenAICompatibleProvider("vllm", "http://vllm:8000/v1", "Qwen/Qwen3-8B", "VLLM_API_KEY")
    assert validate_provider(provider) == ()
    assert provider.chat_completions_url == "http://vllm:8000/v1/chat/completions"


def test_provider_rejects_embedded_secret_wrong_path_and_plain_http_in_production():
    provider = OpenAICompatibleProvider("x", "http://model:8000/api", "", "secret=abc", "production")
    errors = validate_provider(provider)
    assert len(errors) == 4
