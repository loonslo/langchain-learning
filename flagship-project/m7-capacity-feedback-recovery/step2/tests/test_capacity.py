import pytest

from customer_support.capacity import report


def test_capacity_fails_on_latency_or_errors():
    assert report([10] * 19 + [3000], [200] * 20).passed is True
    assert report([10] * 20, [200] * 19 + [500]).passed is False


def test_small_sample_p95_keeps_the_slowest_request():
    assert report([10] * 9 + [3000], [200] * 10).passed is False


def test_empty_samples_are_rejected_instead_of_passing():
    with pytest.raises(ValueError):
        report([], [])
