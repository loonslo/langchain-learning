"""FastAPI 边界：把 Day55–60 的统一应用暴露为稳定 JSON 契约。"""

from typing import Protocol
from fastapi import FastAPI
from pydantic import BaseModel, Field
from .application import ApplicationResult
from .assistant import SupportAnswer


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


def create_app(service: Service) -> FastAPI:
    app = FastAPI(title="Customer Support")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest):
        if hasattr(service, "handle"):
            product = service.handle(
                request.question,
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                session_id=request.session_id,
                order_id=request.order_id,
            )
            return ChatResponse(
                answer=product.answer.text,
                sources=list(product.answer.sources),
                ticket_id=product.ticket_id,
            )
        # 兼容 Day51–54 的最小 Assistant，便于旧测试和渐进迁移。
        answer = service.ask(request.question)
        return ChatResponse(answer=answer.text, sources=list(answer.sources))

    return app
