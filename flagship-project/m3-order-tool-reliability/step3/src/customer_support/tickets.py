"""人工升级：证据不足或用户明确要求时创建 open 工单。"""

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    user_id: str
    question: str
    reason: str
    status: str = "open"


class TicketStore:
    """内存工单库。"""

    def __init__(self):
        self.items = {}

    def create(self, user_id, question, reason):
        """创建 open 状态的工单，编号形如 T-xxxxxxxx。"""
        ticket = Ticket(f"T-{uuid4().hex[:8]}", user_id, question, reason)
        self.items[ticket.ticket_id] = ticket
        return ticket


def escalate(store, user_id, question, has_evidence):
    """决定是否升级人工：用户消息含“人工”记 user_requested；没有证据（来源为空）记 insufficient_evidence；
    否则不建单，返回 None。
    """
    reason = (
        "user_requested"
        if "人工" in question
        else "insufficient_evidence"
        if not has_evidence
        else ""
    )
    return store.create(user_id, question, reason) if reason else None
