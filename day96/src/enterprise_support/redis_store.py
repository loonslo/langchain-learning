"""Redis 热路径：缓存必须可失效，限流故障必须显式失败。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol


class RedisLike(Protocol):
    def get(self, key: str) -> bytes | str | None: ...

    def set(self, key: str, value: str, *, ex: int) -> object: ...

    def delete(self, *keys: str) -> object: ...

    def incr(self, key: str) -> int: ...

    def expire(self, key: str, seconds: int) -> object: ...


@dataclass(frozen=True)
class CacheScope:
    tenant_id: str
    knowledge_version: str
    acl_version: str
    model: str


class RedisAnswerCache:
    def __init__(self, redis: RedisLike, *, ttl_seconds: int = 300) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def key(scope: CacheScope, question: str) -> str:
        material = json.dumps({**scope.__dict__, "question": " ".join(question.split())}, sort_keys=True)
        return "answer:" + hashlib.sha256(material.encode()).hexdigest()

    def get(self, scope: CacheScope, question: str) -> str | None:
        value = self.redis.get(self.key(scope, question))
        if value is None:
            return None
        return value.decode() if isinstance(value, bytes) else value

    def set(self, scope: CacheScope, question: str, answer: str) -> None:
        self.redis.set(self.key(scope, question), answer, ex=self.ttl_seconds)


class FixedWindowRateLimiter:
    def __init__(self, redis: RedisLike, *, limit: int, window_seconds: int) -> None:
        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds

    def allow(self, *, tenant_id: str, user_id: str, window: str) -> bool:
        try:
            key = f"rate:{tenant_id}:{user_id}:{window}"
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, self.window_seconds)
            return count <= self.limit
        except Exception as exc:
            raise RuntimeError("限流后端不可用，按失败关闭处理") from exc
