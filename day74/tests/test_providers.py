from customer_support.providers import (
    FallbackChatModel,
    TemporaryProviderError,
    answer_with_fallback,
)


class P:
    def __init__(self, value):
        self.value = value

    def answer(self, prompt):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def test_temporary_failure_uses_fallback():
    assert answer_with_fallback(P(TemporaryProviderError()), P("备用"), "q") == "备用"


def test_langchain_invoke_contract_also_uses_fallback():
    class Model:
        def __init__(self, value):
            self.value = value

        def invoke(self, _messages):
            if isinstance(self.value, Exception):
                raise self.value
            return self.value

    model = FallbackChatModel(Model(TemporaryProviderError()), Model("备用回答"))
    assert model.invoke([]) == "备用回答"
