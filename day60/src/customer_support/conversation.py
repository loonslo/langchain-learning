"""Day60 会话层：保留内存实现，并新增基于 SQLite 的同接口实现。"""

from __future__ import annotations

from dataclasses import dataclass

from .thread_store import Message, SQLiteThreadStore


@dataclass(frozen=True)
class Turn:
    question: str
    answer: str


class History:
    def __init__(self, max_turns: int = 3):
        self.max_turns, self._data = max_turns, {}

    def add(self, session_id: str, turn: Turn, **_scope) -> None:
        turns = self._data.setdefault(session_id, [])
        turns.append(turn)
        del turns[: -self.max_turns]

    def get(self, session_id: str) -> tuple[Turn, ...]:
        return tuple(self._data.get(session_id, ()))

    def standalone(self, session_id: str, question: str, **_scope) -> str:
        turns = self.get(session_id)
        return (
            f"上一问题：{turns[-1].question}\n当前追问：{question}"
            if turns and len(question) <= 12
            else question
        )


class PersistentHistory:
    """把与 History 相同的会话契约落到租户隔离的 SQLite 存储。"""

    def __init__(self, store: SQLiteThreadStore, max_messages: int = 6):
        self.store = store
        self.max_messages = max_messages

    def standalone(
        self,
        session_id: str,
        question: str,
        *,
        tenant_id: str = "local",
        user_id: str = "local",
    ) -> str:
        messages = self.store.load(
            tenant_id, user_id, session_id, limit=self.max_messages
        )
        previous = next(
            (message.content for message in reversed(messages) if message.role == "user"),
            "",
        )
        return (
            f"上一问题：{previous}\n当前追问：{question}"
            if previous and len(question) <= 12
            else question
        )

    def add(
        self,
        session_id: str,
        turn: Turn,
        *,
        tenant_id: str = "local",
        user_id: str = "local",
    ) -> None:
        self.store.append(tenant_id, user_id, session_id, Message("user", turn.question))
        self.store.append(tenant_id, user_id, session_id, Message("assistant", turn.answer))
