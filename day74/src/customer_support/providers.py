"""模型供应商契约与受控 fallback：只对临时故障切换。"""

from typing import Protocol


class Provider(Protocol):
    def answer(self, prompt: str) -> str: ...


class TemporaryProviderError(Exception):
    pass


def answer_with_fallback(primary: Provider, fallback: Provider, prompt: str) -> str:
    try:
        return primary.answer(prompt)
    except TemporaryProviderError:
        return fallback.answer(prompt)


class TransientChatModel:
    """把连接类异常收敛成明确的临时 provider 错误。"""

    def __init__(self, model):
        self.model = model

    def invoke(self, messages):
        try:
            return self.model.invoke(messages)
        except (TimeoutError, ConnectionError) as exc:
            raise TemporaryProviderError(str(exc)) from exc


class FallbackChatModel:
    """保持 LangChain ``invoke`` 契约，只对临时故障调用备用模型。"""

    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    def invoke(self, messages):
        try:
            return self.primary.invoke(messages)
        except TemporaryProviderError:
            return self.fallback.invoke(messages)
