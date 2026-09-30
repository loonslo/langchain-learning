import pytest

from src.enterprise_support.a2a import (
    AgentCard, AgentSkill, InMemoryTaskStore, TaskState, TaskTransitionError,
)


def test_agent_card_advertises_capabilities_without_embedded_secrets():
    card = AgentCard("orders", "查询已授权订单", "https://agents.example/orders", "0.1", (AgentSkill("order-status", "查订单"),))
    payload = card.as_dict()
    assert payload["skills"][0]["id"] == "order-status"
    assert "secret" not in str(payload).lower()


def test_message_id_is_idempotent_and_terminal_task_cannot_restart():
    store = InMemoryTaskStore()
    task = store.submit(message_id="m-1", message={"role": "user", "parts": []})
    assert store.submit(message_id="m-1", message={"role": "user", "parts": []}).id == task.id
    store.transition(task.id, TaskState.WORKING)
    store.transition(task.id, TaskState.COMPLETED)
    with pytest.raises(TaskTransitionError):
        store.transition(task.id, TaskState.WORKING)


def test_working_task_can_require_auth_and_canceled_task_cannot_resume():
    store = InMemoryTaskStore()
    task = store.submit(message_id="m-2", message={"role": "user", "parts": []})
    store.transition(task.id, TaskState.WORKING)
    assert store.transition(task.id, TaskState.AUTH_REQUIRED).state is TaskState.AUTH_REQUIRED
    store.transition(task.id, TaskState.CANCELED)
    with pytest.raises(TaskTransitionError):
        store.transition(task.id, TaskState.WORKING)
