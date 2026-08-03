from customer_support.evidence import missing_evidence


def test_missing_claim_evidence_is_reported(tmp_path):
    (tmp_path / "real.md").write_text("x")
    assert missing_evidence(tmp_path, ["real.md", "fake.md"]) == ["fake.md"]
