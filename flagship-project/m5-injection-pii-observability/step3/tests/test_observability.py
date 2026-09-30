import pytest
from customer_support.observability import Recorder


def test_success_and_failure_are_observed_without_question():
    r = Recorder()
    r.measure("chat", "shop", lambda: "ok")
    with pytest.raises(RuntimeError):
        r.measure("order", "shop", lambda: (_ for _ in ()).throw(RuntimeError()))
    assert [x.status for x in r.records] == ["ok", "error"] and not hasattr(
        r.records[0], "question"
    )
