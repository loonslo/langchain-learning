"""
capstone/api_enterprise.py · 企业版服务：认证 + 多租户 + 权限 + 限流 + /v1 + 监控
==========================================================
整合 Day56（auth/多租户/限流）+ Day55（文档级权限）+ Day62（监控）+ Day66（/v1 + OpenAPI）。
基础版见 api.py；这个是"上岗即用"的整合版，毕业项目对外用它。

跑法（仓库根目录）：
  pip install fastapi uvicorn "python-jose[cryptography]"
  uvicorn capstone.api_enterprise:app --reload
  开 http://127.0.0.1:8000/docs

调用流程：
  1) POST /v1/login 拿 token（演示用，真实系统对接你的账号体系）
  2) 带 Authorization: Bearer <token> 调 /v1/chat
  无 token → 401；超频 → 429；不同租户数据互不可见。
==========================================================
"""

import time
from fastapi import FastAPI, Depends
from pydantic import BaseModel

import config as C
from knowledge_base import KnowledgeBase
from permissions import User, permission_chain
from auth import issue_token, guard
import monitoring

app = FastAPI(title="企业知识库 Agent（企业版）", version="1.0.0")

# 进程内复用一个 KB（演示用单库；真正多租户隔离见 auth.tenant_chroma_dir 的按租户分库）
_kb = KnowledgeBase().build()


class LoginReq(BaseModel):
    user_id: str
    tenant: str = "demo"
    roles: list[str] = ["employee"]
    dept: str = "public"


class ChatReq(BaseModel):
    question: str


class ChatResp(BaseModel):
    answer: str
    tenant: str


@app.post("/v1/login")
def login(req: LoginReq):
    """演示发证：真实系统应校验密码 / 对接 SSO，这里直接签发。"""
    token = issue_token(req.user_id, req.tenant, req.roles, req.dept)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/v1/chat", response_model=ChatResp)
def chat(req: ChatReq, identity: dict = Depends(guard)):
    """认证 + 限流（guard 依赖）后，按用户身份做权限过滤的问答。"""
    user = User(user_id=identity["user_id"], dept=identity["dept"], roles=identity["roles"])
    t0 = time.time()
    err = False
    try:
        ans = permission_chain(_kb, user).invoke(req.question)
    except Exception:
        err = True
        ans = "服务暂时不可用，请稍后再试。"
    finally:
        monitoring.record(identity["tenant"], (time.time() - t0) * 1000, err)
    return ChatResp(answer=ans, tenant=identity["tenant"])


@app.get("/v1/metrics")
def metrics(identity: dict = Depends(guard)):
    """整体健康度看板数据（Day62）。"""
    return monitoring.health()


@app.get("/health")
def health():
    return {"status": "ok"}
