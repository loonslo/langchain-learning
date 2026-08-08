"""把 Day55 会话能力接入 Day51–54 已有的正式问答助手。"""

from __future__ import annotations

from typing import Protocol

from .assistant import SupportAnswer
from .conversation import History, Turn


class Assistant(Protocol):
    def ask(self, question: str) -> SupportAnswer: ...


class SupportApplication:
    """稳定产品入口；后续能力继续在这里编排，而不是各自成为 Demo。"""

    def __init__(self, assistant: Assistant, history: History):
        self.assistant = assistant
        self.history = history

    def ask(
        self,
        question: str,
        *,
        session_id: str = "cli",
        tenant_id: str = "local",
        user_id: str = "local",
    ) -> SupportAnswer:
        standalone = self.history.standalone(
            session_id,
            question,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        answer = self.assistant.ask(standalone)
        self.history.add(
            session_id,
            Turn(question, answer.text),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        return answer
