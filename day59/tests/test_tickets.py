from customer_support.tickets import TicketStore, escalate


def test_missing_evidence_creates_open_ticket_but_answerable_question_does_not():
    store = TicketStore()
    ticket = escalate(store, "alice", "会员权益", False)
    assert ticket.status == "open" and escalate(store, "alice", "退款", True) is None
