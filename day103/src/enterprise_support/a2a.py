"""A2A v0.3 核心数据模型的教学实现。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TaskState(StrEnum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    REJECTED = "rejected"
    AUTH_REQUIRED = "auth-required"


TERMINAL_STATES = frozenset({TaskState.COMPLETED, TaskState.CANCELED, TaskState.FAILED, TaskState.REJECTED})
_TRANSITIONS = {
    TaskState.SUBMITTED: {TaskState.WORKING, TaskState.CANCELED, TaskState.REJECTED, TaskState.AUTH_REQUIRED},
    TaskState.WORKING: {TaskState.INPUT_REQUIRED, TaskState.COMPLETED, TaskState.CANCELED, TaskState.FAILED},
    TaskState.INPUT_REQUIRED: {TaskState.WORKING, TaskState.CANCELED, TaskState.FAILED},
    TaskState.AUTH_REQUIRED: {TaskState.WORKING, TaskState.CANCELED, TaskState.FAILED},
}


@dataclass(frozen=True)
class AgentSkill:
    id: str
    description: str
    input_modes: tuple[str, ...] = ("text/plain",)
    output_modes: tuple[str, ...] = ("text/plain",)


@dataclass(frozen=True)
class AgentCard:
    name: str
    description: str
    url: str
    version: str
    skills: tuple[AgentSkill, ...]
    streaming: bool = False
    authentication_schemes: tuple[str, ...] = ("OAuth2",)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "capabilities": {"streaming": self.streaming},
            "authentication": {"schemes": list(self.authentication_schemes)},
            "skills": [
                {"id": skill.id, "description": skill.description,
                 "inputModes": list(skill.input_modes), "outputModes": list(skill.output_modes)}
                for skill in self.skills
            ],
        }


@dataclass(frozen=True)
class AgentTask:
    id: str
    context_id: str
    message_id: str
    message: dict[str, Any]
    state: TaskState = TaskState.SUBMITTED
    status_message: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "kind": "task", "id": self.id, "contextId": self.context_id,
            "status": {"state": self.state.value, "timestamp": self.updated_at},
            "history": [self.message],
        }
        if self.status_message:
            payload["status"]["message"] = {"role": "agent", "parts": [{"kind": "text", "text": self.status_message}]}
        return payload


class TaskNotFound(KeyError):
    pass


class TaskTransitionError(ValueError):
    pass


class InMemoryTaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, AgentTask] = {}
        self._by_message_id: dict[str, str] = {}

    def submit(self, *, message_id: str, message: dict[str, Any], context_id: str | None = None) -> AgentTask:
        if not message_id:
            raise ValueError("A2A messageId 不能为空")
        existing_id = self._by_message_id.get(message_id)
        if existing_id:
            return self._tasks[existing_id]
        task = AgentTask(str(uuid4()), context_id or str(uuid4()), message_id, dict(message))
        self._tasks[task.id] = task
        self._by_message_id[message_id] = task.id
        return task

    def get(self, task_id: str) -> AgentTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise TaskNotFound(task_id) from exc

    def transition(self, task_id: str, state: TaskState, status_message: str = "") -> AgentTask:
        previous = self.get(task_id)
        if previous.state in TERMINAL_STATES or state not in _TRANSITIONS.get(previous.state, set()):
            raise TaskTransitionError(f"不允许 {previous.state.value} → {state.value}")
        updated = AgentTask(previous.id, previous.context_id, previous.message_id, previous.message, state, status_message)
        self._tasks[task_id] = updated
        return updated
