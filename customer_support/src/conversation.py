"""保存同一会话的近期问答记录。

这是一个内存版历史记录：程序关闭后数据会消失。它适合本地学习和命令行演示，
尚未实现数据库持久化、租户隔离或并发控制。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Turn:
    """一次问答的最小记录：用户问题和助手回答。"""

    question: str
    answer: str


class History:
    """按 ``session_id`` 保存有限数量的最近对话轮次。"""

    def __init__(self, max_turns: int = 3):
        if max_turns < 1:
            raise ValueError("max_turns 必须大于 0")
        self.max_turns = max_turns
        self._data: dict[str, list[Turn]] = {}

    def add(
        self,
        session_id: str,
        turn: Turn,
        *,
        tenant_id: str = "local",
        user_id: str = "local",
    ) -> None:
        """记录本轮对话，仅保留该会话最新的 ``max_turns`` 条。"""
        # tenant_id 和 user_id 为后续存储层预留；当前内存字典只按 session_id 分组。
        del tenant_id, user_id
        turns = self._data.setdefault(session_id, [])
        turns.append(turn)
        del turns[: -self.max_turns]

    def get(self, session_id: str) -> tuple[Turn, ...]:
        """取得某个会话的历史副本，调用者不能直接改写内部列表。"""
        return tuple(self._data.get(session_id, ()))

    def standalone(
        self,
        session_id: str,
        question: str,
        *,
        tenant_id: str = "local",
        user_id: str = "local",
    ) -> str:
        """为不超过 12 个字符的短追问补上上一轮问题。"""
        del tenant_id, user_id
        turns = self.get(session_id)
        if turns and len(question) <= 12:
            return f"上一个问题：{turns[-1].question}\n当前追问：{question}"
        return question
