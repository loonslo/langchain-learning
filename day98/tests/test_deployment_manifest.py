from pathlib import Path

from src.enterprise_support.runtime import RuntimeSettings, configuration_errors


def test_compose_keeps_dependency_ports_on_loopback_and_has_persistent_volumes():
    compose = Path("compose.yaml").read_text(encoding="utf-8")
    assert '"127.0.0.1:${POSTGRES_PORT:-5432}:5432"' in compose
    assert "postgres-data:" in compose and "qdrant-data:" in compose


def test_production_configuration_rejects_example_secret():
    errors = configuration_errors(RuntimeSettings(
        "postgresql://u:change-me@postgres/db", "redis://redis:6379/0", "http://qdrant:6333", "production"
    ))
    assert errors == ("生产环境禁止使用示例数据库密码",)
