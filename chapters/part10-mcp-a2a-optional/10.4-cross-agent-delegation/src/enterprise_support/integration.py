"""客服 Agent 委托订单 Agent 的最小集成；委托上下文不包含数据库凭据或 bearer token。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from .a2a import TaskState
from .a2a_api import A2AApplication, AgentOutcome
from .slots import extract_slots


@dataclass(frozen=True)
class DelegationContext:
    """委托上下文：租户、主体、scope 和请求 ID，不含数据库凭据或令牌。as_metadata() 会随消息发送，
    但接收方不能据此授权，身份要由认证令牌确定。
    """

    tenant_id: str
    subject: str
    scopes: tuple[str, ...]
    request_id: str

    def as_metadata(self) -> dict[str, object]:
        return {"tenantId": self.tenant_id, "subject": self.subject, "scopes": list(self.scopes), "requestId": self.request_id}


class OrderReader(Protocol):
    """订单读取接口；真实实现在订单服务内，按租户和主体过滤。"""

    def status(self, *, tenant_id: str, subject: str, order_id: str) -> str: ...


class OrderAgent:
    def __init__(self, reader: OrderReader, context: DelegationContext) -> None:
        self.reader = reader
        self.context = context

    def handle(self, text: str) -> AgentOutcome:
        """从文本提取订单号：缺订单号返回 input-required；上下文没有 orders.read 返回 auth-required；
        否则读取订单状态并完成。身份和 scope 来自构造时传入的 context，而不是请求里的 metadata。
        """
        order_id = extract_slots(text).get("order_id")
        if not order_id:
            return AgentOutcome(TaskState.INPUT_REQUIRED, "请提供订单号后再查询。")
        if "orders.read" not in self.context.scopes:
            return AgentOutcome(TaskState.AUTH_REQUIRED, "当前委托没有 orders.read 权限。")
        status = self.reader.status(tenant_id=self.context.tenant_id, subject=self.context.subject, order_id=order_id)
        return AgentOutcome(TaskState.COMPLETED, f"订单 {order_id} 当前状态：{status}")


class InProcessA2AClient:
    """测试替身；真实版本用 HTTPS 调远端 Agent Card 声明的 endpoint。"""

    def __init__(self, application: A2AApplication) -> None:
        self.application = application

    def send_order_question(self, text: str, context: DelegationContext) -> dict[str, object]:
        payload = {
            "jsonrpc": "2.0", "id": context.request_id, "method": "message/send",
            "params": {"message": {"role": "user", "messageId": str(uuid4()), "parts": [{"kind": "text", "text": text}]}, "metadata": context.as_metadata()},
        }
        return self.application.dispatch(payload)


class SupportOrderDelegator:
    def __init__(self, client: InProcessA2AClient) -> None:
        self.client = client

    def handle(self, question: str, context: DelegationContext) -> str:
        """把问题委托给订单 Agent 并翻译结果：JSON-RPC 错误 → 转人工提示；input-required → 原样追问；
        auth-required → 无权限提示；其余返回订单 Agent 的说明。
        """
        response = self.client.send_order_question(question, context)
        if "error" in response:
            return "订单服务暂时不可用，已转人工处理。"
        task = response["result"]
        status = task["status"]
        message = status.get("message", {}).get("parts", [{}])[0].get("text", "")
        if status["state"] == TaskState.INPUT_REQUIRED.value:
            return message
        if status["state"] == TaskState.AUTH_REQUIRED.value:
            return "当前账号无权查询该订单，请联系人工客服。"
        return message
