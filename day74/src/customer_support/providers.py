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
