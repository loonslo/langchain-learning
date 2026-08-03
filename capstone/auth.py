"""JWT 验证、租户标识和可替换的限流后端。"""

from __future__ import annotations

import logging
import os
import secrets
import time
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from threading import Lock

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import InvalidTokenError

from . import config as C
from .permissions import User

LOG = logging.getLogger(__name__)
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ISSUER = os.getenv("JWT_ISSUER", "capstone-local")
AUDIENCE = os.getenv("JWT_AUDIENCE", "capstone-api")
TOKEN_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "3600"))
ENABLE_DEV_LOGIN = (
    os.getenv("CAPSTONE_ENABLE_DEV_LOGIN", "false").strip().lower() == "true"
)
_EPHEMERAL_SECRET = secrets.token_urlsafe(48)


def _secret() -> str:
    configured = os.getenv("JWT_SECRET", "")
    if configured:
        return configured
    if C.APP_ENV == "production":
        raise RuntimeError("生产环境必须配置 JWT_SECRET")
    return _EPHEMERAL_SECRET


def auth_configuration_errors() -> list[str]:
    errors: list[str] = []
    secret = os.getenv("JWT_SECRET", "")
    if ALGORITHM != "HS256":
        errors.append("当前实现仅允许显式 HS256；外部 IdP 应接入 JWKS 验证器")
    if C.APP_ENV == "production" and len(secret) < 32:
        errors.append("生产 JWT_SECRET 至少需要 32 个字符")
    if C.APP_ENV == "production" and ENABLE_DEV_LOGIN:
        errors.append("生产环境禁止 CAPSTONE_ENABLE_DEV_LOGIN")
    if TOKEN_TTL_SECONDS <= 0 or TOKEN_TTL_SECONDS > 86400:
        errors.append("JWT_TTL_SECONDS 必须在 1-86400 秒之间")
    if C.APP_ENV == "production" and not os.getenv("REDIS_URL"):
        errors.append("生产多实例限流必须配置 REDIS_URL")
    return errors


def issue_token(
    user_id: str,
    tenant: str,
    roles: list[str],
    dept: str = "",
    *,
    ttl_seconds: int | None = None,
) -> str:
    """为本地开发/测试签发 token；生产登录端点不会调用此函数。"""
    identity = User(
        user_id=user_id,
        tenant_id=tenant,
        dept=dept,
        roles=frozenset(roles),
    )
    now = datetime.now(UTC)
    ttl = ttl_seconds or TOKEN_TTL_SECONDS
    payload = {
        "sub": identity.user_id,
        "tenant": identity.tenant_id,
        "roles": sorted(identity.roles),
        "dept": identity.dept,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> User:
    try:
        claims = jwt.decode(
            token,
            _secret(),
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require": ["sub", "tenant", "iss", "aud", "iat", "exp", "jti"]
            },
        )
        roles = claims.get("roles", [])
        if not isinstance(roles, list) or not all(
            isinstance(role, str) for role in roles
        ):
            raise ValueError("roles claim 必须是字符串数组")
        return User(
            user_id=claims["sub"],
            tenant_id=claims["tenant"],
            dept=claims.get("dept", ""),
            roles=frozenset(roles),
        )
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=401,
            detail="token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def current_identity(authorization: str = Header(default="")) -> User:
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail="缺少 Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(token.strip())


def tenant_chroma_dir(tenant: str) -> str:
    return str(C.tenant_chroma_dir(tenant))


class RateLimitExceeded(RuntimeError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("rate limit exceeded")
        self.retry_after = max(1, retry_after)


class InMemoryRateLimiter:
    """线程安全的单进程滑动窗口；仅供本地开发和单 worker 部署。"""

    def __init__(self, max_per_minute: int = 30) -> None:
        if max_per_minute <= 0:
            raise ValueError("max_per_minute 必须大于 0")
        self.max = max_per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, tenant: str) -> None:
        now = time.monotonic()
        with self._lock:
            queue = self.hits[tenant]
            while queue and now - queue[0] >= 60:
                queue.popleft()
            if len(queue) >= self.max:
                raise RateLimitExceeded(int(60 - (now - queue[0])) + 1)
            queue.append(now)


class RedisRateLimiter:
    """通过 Redis 原子 Lua 脚本实现跨 worker 固定窗口限流。"""

    _SCRIPT = """
    local current = redis.call('INCR', KEYS[1])
    if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
    local ttl = redis.call('TTL', KEYS[1])
    return {current, ttl}
    """

    def __init__(self, redis_url: str, max_per_minute: int = 30) -> None:
        import redis

        self.client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.max = max_per_minute
        self.script = self.client.register_script(self._SCRIPT)

    def check(self, tenant: str) -> None:
        bucket = int(time.time() // 60)
        current, ttl = self.script(
            keys=[f"capstone:rate:{tenant}:{bucket}"],
            args=[60],
        )
        if int(current) > self.max:
            raise RateLimitExceeded(int(ttl))


RateLimiter = InMemoryRateLimiter


@lru_cache(maxsize=1)
def get_rate_limiter() -> InMemoryRateLimiter | RedisRateLimiter:
    maximum = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return RedisRateLimiter(redis_url, maximum)
    if C.APP_ENV == "production":
        raise RuntimeError("生产环境必须使用 REDIS_URL 配置分布式限流")
    LOG.warning("使用单进程内存限流；仅适用于本地开发")
    return InMemoryRateLimiter(maximum)


def guard(identity: User = Depends(current_identity)) -> User:
    try:
        get_rate_limiter().check(identity.tenant_id)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    return identity


if __name__ == "__main__":
    if auth_configuration_errors():
        print("配置问题：", auth_configuration_errors())
    token = issue_token(
        "alice",
        tenant="acme",
        roles=["employee", "finance"],
        dept="finance",
    )
    identity = decode_token(token)
    print(
        "身份：",
        {
            "user_id": identity.user_id,
            "tenant": identity.tenant_id,
            "roles": sorted(identity.roles),
            "dept": identity.dept,
        },
    )
    print("租户向量库：", tenant_chroma_dir(identity.tenant_id))
    limiter = InMemoryRateLimiter(max_per_minute=2)
    for index in range(3):
        try:
            limiter.check("acme")
            print(f"第 {index + 1} 次：放行")
        except RateLimitExceeded as exc:
            print(f"第 {index + 1} 次：限流，{exc.retry_after}s 后重试")
