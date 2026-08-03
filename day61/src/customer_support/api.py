"""FastAPI 边界：用稳定 JSON 契约暴露客服能力。"""

from typing import Protocol
from fastapi import FastAPI
from pydantic import BaseModel, Field
from .assistant import SupportAnswer


class Service(Protocol):
    def ask(self, question: str) -> SupportAnswer: ...


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


def create_app(service: Service) -> FastAPI:
    app = FastAPI(title="Customer Support")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest):
        result = service.ask(request.question)
        return ChatResponse(answer=result.text, sources=list(result.sources))

    return app
