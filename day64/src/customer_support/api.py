"""Day64 API：问答链不变，并新增可观察的知识增量同步计划。"""

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .auth import AuthenticationError, TokenVerifier


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    tenant_id: str = "public"
    user_id: str = "anonymous"
    session_id: str = "default"
    order_id: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    ticket_id: str | None = None


class SyncRequest(BaseModel):
    previous: dict[str, str] = Field(default_factory=dict)


def create_app(service, verifier: TokenVerifier | None = None) -> FastAPI:
    app = FastAPI(title="Customer Support")

    def identity(authorization: str, request: ChatRequest | None = None):
        if verifier is None:
            return (
                request.tenant_id if request else "public",
                request.user_id if request else "anonymous",
            )
        try:
            verified = verifier.verify(authorization)
            return verified.tenant_id, verified.user_id
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
        tenant_id, user_id = identity(authorization, request)
        if hasattr(service, "handle"):
            result = service.handle(
                request.question,
                tenant_id=tenant_id,
                user_id=user_id,
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

    @app.post("/knowledge/sync-plan")
    def sync_plan(request: SyncRequest, authorization: str = Header(default="")):
        identity(authorization)
        result = service.plan_sync(request.previous)
        return {"upsert": list(result.upsert), "delete": list(result.delete)}

    return app
