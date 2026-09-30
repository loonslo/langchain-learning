from ai_testing.resilience import RetryPolicy, call_with_retry, meets_slo, percentile, validate_input


def test_retry_is_finite_and_records_attempt_count():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise TimeoutError("upstream")
        return "ok"

    result, attempts, error = call_with_retry(flaky, RetryPolicy(3), sleep=lambda _: None)

    assert (result, attempts, error) == ("ok", 3, None)


def test_input_guard_and_slo_fail_closed():
    assert "问题不能为空" in validate_input(" ")
    assert any("问题超过长度限制" in error for error in validate_input("x" * 6, max_length=5))
    assert meets_slo([100, 120, 150, 180, 200], 0.01, 200, 0.02)
    tail_latency_samples = [100, 120, 150, 180] + [200] * 14 + [500, 500]
    assert not meets_slo(tail_latency_samples, 0.01, 200, 0.02)


def test_retry_policy_rejects_invalid_budget():
    try:
        RetryPolicy(0)
    except ValueError as error:
        assert "重试次数" in str(error)
    else:
        raise AssertionError("invalid retry policy should fail")


def test_percentile_keeps_the_slowest_request_for_small_samples():
    assert percentile([100, 900], 0.95) == 900
    assert percentile(list(range(1, 11)), 0.95) == 10
    assert percentile([100, 200, 300, 400], 0.5) == 200
