from src.enterprise_support.contracts import Intent, IntentDecision
from src.enterprise_support.workflow import CustomerWorkflow


class Classifier:
    def classify(self, question):
        if "退款" in question:
            return IntentDecision(Intent.REFUND_STATUS, 0.98)
        return IntentDecision(Intent.UNKNOWN, 0.2)


def test_workflow_asks_once_then_uses_next_turn_as_slot_value():
    workflow = CustomerWorkflow(Classifier())
    first = workflow.handle("t1", "退款什么时候到")
    assert first.status == "needs_slot"

    second = workflow.handle("t1", "订单 A100")
    assert second.status == "ready"
    assert second.slots == {"order_id": "A100"}
    assert workflow.state.get("t1") is None


def test_low_confidence_never_executes_a_business_flow():
    reply = CustomerWorkflow(Classifier()).handle("t2", "给我一个惊喜")
    assert reply.status == "handoff"
    assert reply.intent is Intent.HUMAN_HANDOFF
