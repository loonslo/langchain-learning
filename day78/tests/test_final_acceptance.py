from customer_support.acceptance import REQUIRED, accept


def test_every_required_capability_must_pass():
    results = {name: True for name in REQUIRED}
    assert accept(results)["passed"]
    results["order_isolation"] = False
    assert accept(results) == {"passed": False, "failed": ["order_isolation"]}
