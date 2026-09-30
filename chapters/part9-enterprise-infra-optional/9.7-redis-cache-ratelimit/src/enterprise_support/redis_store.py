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
    """缓存作用域：租户、知识版本、权限版本和模型。acl_version 必须能区分不同权限视图
    （例如角色集合的哈希），否则权限不同的用户会共用同一条缓存答案。
    """

    tenant_id: str
    knowledge_version: str
    acl_version: str
    model: str


class RedisAnswerCache:
    """带 TTL 的答案缓存；键由作用域和规范化后的问题决定。Redis 出错时直接抛出，不做降级。"""

    def __init__(self, redis: RedisLike, *, ttl_seconds: int = 300) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def key(scope: CacheScope, question: str) -> str:
        """缓存键 = 作用域 + 问题（合并连续空白）的 SHA-256；任何一项变化都得到新键，旧答案自然失效。"""
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
    """固定窗口限流：同一 (tenant, user, window) 计数，超过 limit 就拒绝。"""

    def __init__(self, redis: RedisLike, *, limit: int, window_seconds: int) -> None:
        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds

    def allow(self, *, tenant_id: str, user_id: str, window: str) -> bool:
        """返回本次请求是否放行。window 是调用方给出的窗口标识（例如 int(time.time() // 60)），过期靠 TTL。

        Redis 出错时抛 RuntimeError（失败关闭），不会放开限流。incr 和 expire 不是原子操作：
        进程恰好在两步之间崩溃会留下永不过期的计数键，生产环境应改用 Lua 脚本或原子命令。
        """
        try:
            key = f"rate:{tenant_id}:{user_id}:{window}"
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, self.window_seconds)
            return count <= self.limit
        except Exception as exc:
            raise RuntimeError("限流后端不可用，按失败关闭处理") from exc
