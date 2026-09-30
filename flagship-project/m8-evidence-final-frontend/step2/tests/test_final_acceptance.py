from customer_support.acceptance import (
    REQUIRED,
    accept,
    build_offline_checks,
    run_acceptance,
)


def test_every_required_capability_must_pass():
    results = {name: True for name in REQUIRED}
    assert accept(results)["passed"]
    results["order_isolation"] = False
    assert accept(results) == {"passed": False, "failed": ["order_isolation"]}


def test_final_acceptance_executes_checks_and_fails_closed():
    calls = []
    checks = {
        name: (lambda capability=name: calls.append(capability) or True)
        for name in REQUIRED
    }
    checks["backup"] = lambda: (_ for _ in ()).throw(RuntimeError("restore failed"))

    result = run_acceptance(checks)

    assert result == {"passed": False, "failed": ["backup"]}
    assert set(calls) == set(REQUIRED) - {"backup"}


def test_repository_offline_acceptance_reaches_real_components(tmp_path):
    assert run_acceptance(build_offline_checks(tmp_path)) == {
        "passed": True,
        "failed": [],
    }
