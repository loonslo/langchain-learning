"""有边界的会话历史：支持短追问，同时隔离不同 session。"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Turn:
    question: str
    answer: str


class History:
    def __init__(self, max_turns: int = 3):
        self.max_turns, self._data = max_turns, {}

    def add(
        self,
        session_id: str,
        turn: Turn,
        *,
        tenant_id: str = "local",
        user_id: str = "local",
    ) -> None:
        turns = self._data.setdefault(session_id, [])
        turns.append(turn)
        del turns[: -self.max_turns]

    def get(self, session_id: str) -> tuple[Turn, ...]:
        return tuple(self._data.get(session_id, ()))

    def standalone(
        self,
        session_id: str,
        question: str,
        *,
        tenant_id: str = "local",
        user_id: str = "local",
    ) -> str:
        turns = self.get(session_id)
        return (
            f"上一问题：{turns[-1].question}\n当前追问：{question}"
            if turns and len(question) <= 12
            else question
        )
