from customer_support.capacity import report


def test_capacity_fails_on_latency_or_errors():
    assert report([10] * 19 + [3000], [200] * 20).passed is True
    assert report([10] * 20, [200] * 19 + [500]).passed is False
