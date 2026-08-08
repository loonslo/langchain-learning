"""Day63 API：可信身份来自 Bearer token，不再相信请求正文自报用户。"""

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .auth import AuthenticationError, TokenVerifier


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


def create_app(service, verifier: TokenVerifier | None = None) -> FastAPI:
    """传入 verifier 时强制认证；None 仅保留给 Day61–62 兼容测试。"""

    app = FastAPI(title="Customer Support")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(
        request: ChatRequest,
        authorization: str = Header(default=""),
        idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    ):
        if verifier is not None:
            try:
                identity = verifier.verify(authorization)
            except AuthenticationError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
            tenant_id, user_id = identity.tenant_id, identity.user_id
        else:
            tenant_id, user_id = request.tenant_id, request.user_id

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

    return app
