from customer_support.readiness import release_readiness
from customer_support.settings import Settings


def test_capacity_result_enters_the_release_readiness_gate(tmp_path):
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    settings = Settings(knowledge, "embed", "ollama", "model", "url", "")

    errors = release_readiness(settings, [3000] * 20, [200] * 20)

    assert errors and errors[0].startswith("capacity_failed")
