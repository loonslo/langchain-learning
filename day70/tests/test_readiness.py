from customer_support.readiness import readiness
from customer_support.settings import Settings


def test_missing_runtime_requirements_block_readiness(tmp_path):
    s = Settings(tmp_path / "missing.md", "embed", "deepseek", "model", "url", "")
    assert readiness(s) == ["knowledge_missing", "api_key_missing"]
