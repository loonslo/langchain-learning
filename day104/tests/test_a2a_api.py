from src.enterprise_support.a2a import AgentCard, AgentSkill, InMemoryTaskStore, TaskState
from src.enterprise_support.a2a_api import A2AApplication, AgentOutcome


def app():
    card = AgentCard("orders", "订单", "https://agents.example/orders", "0.1", (AgentSkill("order-status", "查询订单"),), streaming=True)
    return A2AApplication(card, InMemoryTaskStore(), lambda text: AgentOutcome(TaskState.COMPLETED, f"已处理：{text}"))


def test_jsonrpc_uses_current_message_send_and_tasks_get_methods():
    application = app()
    sent = application.dispatch({
        "jsonrpc": "2.0", "id": "r1", "method": "message/send",
        "params": {"message": {"role": "user", "messageId": "m1", "parts": [{"kind": "text", "text": "查订单 A100"}]}},
    })
    task_id = sent["result"]["id"]
    fetched = application.dispatch({"jsonrpc": "2.0", "id": "r2", "method": "tasks/get", "params": {"id": task_id}})
    assert fetched["result"]["status"]["state"] == "completed"


def test_jsonrpc_error_and_sse_frame_are_protocol_shaped():
    application = app()
    assert application.dispatch({"jsonrpc": "2.0", "id": 1, "method": "tasks/send", "params": {}})["error"]["code"] == -32601
    task = application.send({"message": {"role": "user", "messageId": "m2", "parts": [{"kind": "text", "text": "查订单"}]}})
    assert next(application.sse("r3", task)).startswith("data: {\"jsonrpc\": \"2.0\"")
