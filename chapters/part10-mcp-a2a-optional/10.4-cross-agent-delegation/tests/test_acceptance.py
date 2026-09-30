from src.enterprise_support.acceptance import run


def test_final_offline_acceptance_passes_core_enterprise_capabilities():
    assert run() == {"intent_slots": True, "json": True, "qdrant_scope": True, "a2a": True}
