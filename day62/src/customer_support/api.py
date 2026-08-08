"""Day62 API：通过 Idempotency-Key 把客户端重试传入写路径。"""

from typing import Protocol

from fastapi import FastAPI, Header
from pydantic import BaseModel, Field

from .application import ApplicationResult


class Service(Protocol):
    def handle(self, question: str, **kwargs) -> ApplicationResult: ...


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    tenant_id: str = Field(default="public", min_length=1, max_length=50)
    user_id: str = Field(default="anonymous", min_length=1, max_length=50)
    session_id: str = Field(default="default", min_length=1, max_length=50)
    order_id: str = Field(default="", max_length=50)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    ticket_id: str | None = None


def create_app(service) -> FastAPI:
    app = FastAPI(title="Customer Support")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(
        request: ChatRequest,
        idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    ):
        if hasattr(service, "handle"):
            result = service.handle(
                request.question,
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                session_id=request.session_id,
                order_id=request.order_id,
                idempotency_key=idempotency_key,
            )
            return ChatResponse(
                answer=result.answer.text,
                sources=list(result.answer.sources),
                ticket_id=result.ticket_id,
            )
        answer = service.ask(request.question)
        return ChatResponse(answer=answer.text, sources=list(answer.sources))

    return app
