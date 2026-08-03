"""最终 HTTP 边界：认证后把知识问答、订单查询和人工升级交给统一应用。"""

from __future__ import annotations
from typing import Protocol
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from .application import ApplicationResult
from .auth import AuthenticationError, Identity, TokenVerifier


class Application(Protocol):
    def handle(
        self, identity: Identity, question: str, version: str = "v1", order_id: str = ""
    ) -> ApplicationResult: ...


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    order_id: str = Field(default="", max_length=50)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    ticket_id: str | None


def create_app(service: Application, verifier: TokenVerifier) -> FastAPI:
    """创建 API；客户端自报身份不会进入业务层。"""
    app = FastAPI(title="Customer Support Copilot", version="1.0.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(
        request: ChatRequest, authorization: str = Header(default="")
    ) -> ChatResponse:
        try:
            identity = verifier.verify(authorization)
            result = service.handle(
                identity, request.question, order_id=request.order_id
            )
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return ChatResponse(
            answer=result.answer.text,
            sources=list(result.answer.sources),
            ticket_id=result.ticket_id,
        )

    return app
