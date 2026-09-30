"""A2A v0.3 的最小 HTTP / JSON-RPC 边界，不依赖某个 Agent 框架。"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from .a2a import AgentCard, AgentTask, InMemoryTaskStore, TaskNotFound, TaskState, TaskTransitionError


@dataclass(frozen=True)
class AgentOutcome:
    state: TaskState
    message: str


class A2AApplication:
    """把任务仓储和处理函数包装成 A2A 方法；handler(text) 返回任务的下一状态和说明文字。"""

    def __init__(self, card: AgentCard, store: InMemoryTaskStore, handler: Callable[[str], AgentOutcome]) -> None:
        self.card = card
        self.store = store
        self.handler = handler

    @staticmethod
    def _text(message: Mapping[str, Any]) -> str:
        if message.get("role") != "user" or not isinstance(message.get("parts"), list):
            raise ValueError("message 必须是含 parts 的 user 消息")
        texts = [part.get("text", "") for part in message["parts"] if isinstance(part, Mapping) and part.get("kind") == "text"]
        text = "\n".join(value for value in texts if isinstance(value, str)).strip()
        if not text:
            raise ValueError("A2A message 必须有 text part")
        return text

    def send(self, params: Mapping[str, Any]) -> AgentTask:
        """message/send：提交消息并同步执行 handler；重复的 messageId 直接返回已有任务，不再执行。"""
        message = params.get("message")
        if not isinstance(message, Mapping):
            raise ValueError("message/send 缺少 message")
        text = self._text(message)
        message_id = str(message.get("messageId", ""))
        task = self.store.submit(message_id=message_id, message=dict(message), context_id=message.get("contextId"))
        if task.state is not TaskState.SUBMITTED:
            return task
        self.store.transition(task.id, TaskState.WORKING, "订单 Agent 正在处理")
        outcome = self.handler(text)
        return self.store.transition(task.id, outcome.state, outcome.message)

    def get(self, task_id: str) -> AgentTask:
        return self.store.get(task_id)

    def cancel(self, task_id: str) -> AgentTask:
        return self.store.transition(task_id, TaskState.CANCELED, "任务已由客户端取消")

    def dispatch(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """处理一个 JSON-RPC 请求，返回响应字典。错误码：-32600 请求无效，-32601 方法不存在，
        -32602 参数错误，-32001 任务不存在。
        """
        request_id = payload.get("id")
        if payload.get("jsonrpc") != "2.0" or "method" not in payload:
            return _error(request_id, -32600, "Invalid Request")
        params = payload.get("params", {})
        if not isinstance(params, Mapping):
            return _error(request_id, -32602, "Invalid params")
        try:
            if payload["method"] == "message/send":
                result = self.send(params).as_dict()
            elif payload["method"] == "tasks/get":
                result = self.get(str(params["id"])).as_dict()
            elif payload["method"] == "tasks/cancel":
                result = self.cancel(str(params["id"])).as_dict()
            else:
                return _error(request_id, -32601, "Method not found")
        except TaskNotFound:  # 它是 KeyError 的子类，必须先捕获，否则会被误报成参数错误
            return _error(request_id, -32001, "Task not found")
        except KeyError:
            return _error(request_id, -32602, "Invalid params")
        except (ValueError, TaskTransitionError) as exc:
            return _error(request_id, -32602, str(exc))
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def sse(self, request_id: str | int | None, task: AgentTask) -> Iterator[str]:
        """把任务快照编码成一帧 SSE。本章的任务同步完成，所以只有一帧，不是增量推送。"""
        event = {"jsonrpc": "2.0", "id": request_id, "result": task.as_dict()}
        yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


def _error(request_id: object, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def create_fastapi_app(application: A2AApplication):
    """延迟导入 Web 框架，让协议单元测试不需要服务进程。"""
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import StreamingResponse

    app = FastAPI(title=application.card.name)

    @app.get("/.well-known/agent.json")
    def agent_card():
        return application.card.as_dict()

    @app.post("/")
    def jsonrpc(payload: dict[str, Any]):
        return application.dispatch(payload)

    @app.post("/v1/message:send")
    def send(payload: dict[str, Any]):
        try:
            return {"task": application.send(payload).as_dict()}
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/v1/tasks/{task_id}")
    def task(task_id: str):
        try:
            return application.get(task_id).as_dict()
        except TaskNotFound as exc:
            raise HTTPException(404, "task not found") from exc

    @app.post("/v1/message:stream")
    def stream(payload: dict[str, Any]):
        try:
            task = application.send(payload)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return StreamingResponse(application.sse(payload.get("id"), task), media_type="text/event-stream")

    return app
