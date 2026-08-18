from src.enterprise_support.a2a import AgentCard, AgentSkill, InMemoryTaskStore
from src.enterprise_support.a2a_api import A2AApplication
from src.enterprise_support.integration import DelegationContext, InProcessA2AClient, OrderAgent, SupportOrderDelegator


class Reader:
    def status(self, *, tenant_id, subject, order_id):
        assert (tenant_id, subject, order_id) == ("shop-a", "u1", "A100")
        return "运输中"


def test_support_agent_delegates_without_exposing_database_credentials():
    context = DelegationContext("shop-a", "u1", ("orders.read",), "r1")
    agent = OrderAgent(Reader(), context)
    card = AgentCard("orders", "订单", "https://agents.example/orders", "0.1", (AgentSkill("order-status", "查订单"),))
    delegator = SupportOrderDelegator(InProcessA2AClient(A2AApplication(card, InMemoryTaskStore(), agent.handle)))
    assert delegator.handle("订单 A100 到哪里了", context) == "订单 A100 当前状态：运输中"
    assert "token" not in str(context.as_metadata()).lower()


def test_order_agent_asks_for_missing_slot_instead_of_guessing():
    context = DelegationContext("shop-a", "u1", ("orders.read",), "r2")
    agent = OrderAgent(Reader(), context)
    card = AgentCard("orders", "订单", "https://agents.example/orders", "0.1", (AgentSkill("order-status", "查订单"),))
    result = SupportOrderDelegator(InProcessA2AClient(A2AApplication(card, InMemoryTaskStore(), agent.handle))).handle("帮我查订单", context)
    assert result == "请提供订单号后再查询。"
