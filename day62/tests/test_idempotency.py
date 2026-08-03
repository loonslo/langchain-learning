import pytest
from customer_support.idempotency import IdempotencyConflict, IdempotencyStore


def test_write_runs_once_and_key_cannot_change_meaning():
    store = IdempotencyStore()
    calls = []

    def op():
        calls.append(1)
        return "T1"
    assert (
        store.execute("k", {"q": "a"}, op) == store.execute("k", {"q": "a"}, op)
        and len(calls) == 1
    )
    with pytest.raises(IdempotencyConflict):
        store.execute("k", {"q": "b"}, op)
