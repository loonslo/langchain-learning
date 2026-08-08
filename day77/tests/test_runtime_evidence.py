import pytest

from customer_support import runtime


def test_runtime_evidence_gate_rejects_an_unverifiable_claim(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime, "PROJECT_ROOT", tmp_path)

    with pytest.raises(RuntimeError, match="fake.md"):
        runtime.verify_project_evidence(["fake.md"])
