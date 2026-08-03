from customer_support.tool_runner import TransientToolError, call_read_only


def test_transient_error_retries_with_hard_limit():
    calls = []

    def op():
        calls.append(1)
        if len(calls) < 2:
            raise TransientToolError("503")
        return "ok"

    assert call_read_only(op).attempts == 2
