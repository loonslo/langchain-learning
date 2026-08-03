from customer_support.providers import TemporaryProviderError, answer_with_fallback


class P:
    def __init__(self, value):
        self.value = value

    def answer(self, prompt):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def test_temporary_failure_uses_fallback():
    assert answer_with_fallback(P(TemporaryProviderError()), P("备用"), "q") == "备用"
