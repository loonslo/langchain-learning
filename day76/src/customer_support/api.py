"""Day76 最终 HTTP 边界：认证身份进入统一应用，并保留同步运维入口。"""

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .auth import AuthenticationError, TokenVerifier


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    session_id: str = Field(default="default", min_length=1, max_length=50)
    order_id: str = Field(default="", max_length=50)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    ticket_id: str | None = None


class SyncRequest(BaseModel):
    previous: dict[str, str] = Field(default_factory=dict)


def create_app(service, verifier: TokenVerifier) -> FastAPI:
    app = FastAPI(title="Customer Support Copilot", version="1.0.0")

    def verify(authorization: str):
        try:
            return verifier.verify(authorization)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(
        request: ChatRequest,
        authorization: str = Header(default=""),
        idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    ):
        identity = verify(authorization)
        result = service.handle(
            request.question,
            tenant_id=identity.tenant_id,
            user_id=identity.user_id,
            session_id=request.session_id,
            order_id=request.order_id,
            idempotency_key=idempotency_key,
        )
        return ChatResponse(
            answer=result.answer.text,
            sources=list(result.answer.sources),
            ticket_id=result.ticket_id,
        )

    @app.post("/knowledge/sync-plan")
    def sync_plan(request: SyncRequest, authorization: str = Header(default="")):
        verify(authorization)
        result = service.plan_sync(request.previous)
        return {"upsert": list(result.upsert), "delete": list(result.delete)}

    return app
