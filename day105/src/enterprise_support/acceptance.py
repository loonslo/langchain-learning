"""不需要 Docker、GPU、真实 LLM 的最终关键链路验收。"""

from .a2a import AgentCard, AgentSkill, InMemoryTaskStore
from .a2a_api import A2AApplication
from .integration import DelegationContext, InProcessA2AClient, OrderAgent, SupportOrderDelegator
from .structured_json import JsonSchema, parse_model_json
from .vector_store import QdrantVectorStore
from .workflow import CustomerWorkflow
from .contracts import Intent, IntentDecision


class _Classifier:
    def classify(self, question):
        return IntentDecision(Intent.REFUND_STATUS if "退款" in question else Intent.UNKNOWN, 0.95)


class _Orders:
    def status(self, **_):
        return "已发货"


def run() -> dict[str, bool]:
    workflow = CustomerWorkflow(_Classifier())
    needs_slot = workflow.handle("s1", "退款进度").status == "needs_slot"
    json_contract = parse_model_json('{"answer":"ok","handoff":false}', JsonSchema({"answer": str, "handoff": bool}))["answer"] == "ok"
    qdrant_filter = QdrantVectorStore.tenant_filter("shop-a")["must"][0]["match"]["value"] == "shop-a"
    context = DelegationContext("shop-a", "u1", ("orders.read",), "r1")
    agent = OrderAgent(_Orders(), context)
    card = AgentCard("orders", "订单", "https://agents.example/orders", "0.1", (AgentSkill("order-status", "查订单"),))
    app = A2AApplication(card, InMemoryTaskStore(), agent.handle)
    delegated = SupportOrderDelegator(InProcessA2AClient(app)).handle("订单 A100 到哪里了", context)
    return {"intent_slots": needs_slot, "json": json_contract, "qdrant_scope": qdrant_filter, "a2a": "已发货" in delegated}
