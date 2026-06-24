"""
capstone/auth.py · 认证 + 多租户 + 限流（Day56）
==========================================================
上线给真实用户用，三件事必须有：
1. 认证：没带合法凭证调不通（这里用 JWT；API key 同理）。
2. 多租户：A 租户绝对查不到 B 租户的数据——隔离要落到数据层，不是 if 判断。
3. 限流：单租户调用频率封顶，防止一个客户打爆整个服务和成本。

为什么多租户隔离不能只靠"查询时加个 tenant 条件"：
那是软隔离，一行代码写漏就串数据。强隔离 = 每个租户独立的向量库 collection /
独立 schema，物理上查不到别人的。这里用"按租户分 Chroma 目录"演示强隔离思路。

依赖：pip install "python-jose[cryptography]"
==========================================================
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import Header, HTTPException, Depends
from jose import jwt, JWTError

import config as C

# 演示密钥：生产从 .env / 密钥管理服务读，绝不进代码/仓库
SECRET = "demo-secret-change-me"
ALGO = "HS256"


# ---- 1. JWT 签发与校验 ----
def issue_token(user_id: str, tenant: str, roles: list[str], dept: str = "") -> str:
    """登录成功后签发 token。把身份和租户都写进去，后续每次请求带着它。"""
    payload = {
        "sub": user_id, "tenant": tenant, "roles": roles, "dept": dept,
        "exp": datetime.utcnow() + timedelta(hours=8),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def current_identity(authorization: str = Header(default="")) -> dict:
    """FastAPI 依赖：从 Authorization: Bearer <token> 解析身份。
    没 token / token 非法 → 401，根本进不了业务逻辑。"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "缺少 Bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        claims = jwt.decode(token, SECRET, algorithms=[ALGO])
    except JWTError as e:
        raise HTTPException(401, f"token 无效：{e}")
    return {"user_id": claims["sub"], "tenant": claims["tenant"],
            "roles": set(claims.get("roles", [])), "dept": claims.get("dept", "")}


# ---- 2. 多租户：按租户隔离向量库目录（强隔离思路）----
def tenant_chroma_dir(tenant: str) -> str:
    """每个租户一个独立 Chroma 目录，物理隔离，查不到别人的。"""
    safe = "".join(ch for ch in tenant if ch.isalnum() or ch in "-_")
    return str(C.HERE / "data" / "tenants" / safe / "chroma")


# ---- 3. 限流：滑动窗口，按租户计数 ----
class RateLimiter:
    """每租户每分钟最多 N 次。超了返回 429，保护服务和成本。"""

    def __init__(self, max_per_minute: int = 30):
        self.max = max_per_minute
        self.hits: dict[str, deque] = defaultdict(deque)

    def check(self, tenant: str):
        now = time.time()
        q = self.hits[tenant]
        while q and now - q[0] > 60:    # 滑出 60 秒窗口
            q.popleft()
        if len(q) >= self.max:
            raise HTTPException(429, f"租户 {tenant} 超过限流（{self.max}/分钟）")
        q.append(now)


limiter = RateLimiter(max_per_minute=30)


def guard(identity: dict = Depends(current_identity)) -> dict:
    """组合依赖：认证通过 + 没超限流，才放行。api.py 直接挂这个。"""
    limiter.check(identity["tenant"])
    return identity


if __name__ == "__main__":
    # 演示：签发 + 校验 + 隔离目录 + 限流
    tok = issue_token("alice", tenant="acme", roles=["employee", "finance"], dept="finance")
    print("签发 token：", tok[:40], "...")
    claims = jwt.decode(tok, SECRET, algorithms=[ALGO])
    print("解出身份：", {k: claims[k] for k in ("sub", "tenant", "roles", "dept")})
    print("acme 租户向量库目录：", tenant_chroma_dir("acme"))
    print("evil 租户向量库目录：", tenant_chroma_dir("evil"), "（物理不同目录 → 查不到 acme 的数据）")

    rl = RateLimiter(max_per_minute=2)
    for i in range(3):
        try:
            rl.check("acme"); print(f"第{i+1}次：放行")
        except HTTPException as e:
            print(f"第{i+1}次：被限流 {e.detail}")
