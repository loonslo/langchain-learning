"""L5.8 Redis 缓存/限流 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/redis_store.py。实现下面三组接口，然后运行：

    python chapters/part9-enterprise-infra-optional/9.7-redis-cache-ratelimit/gate/gate_check.py
"""

from __future__ import annotations


def cache_key(scope: dict, question: str) -> str:
    """缓存键 = 作用域 + 合并空白后问题的 SHA-256，前缀 "answer:"。

    scope 至少含 tenant_id/knowledge_version/acl_version/model；
    任一项或问题变化 -> 不同键；question 非字符串 -> ValueError。
    """
    raise NotImplementedError("实现缓存键")


class RedisAnswerCache:
    def __init__(self, redis, ttl_seconds: int = 300):
        raise NotImplementedError("初始化缓存")

    def get(self, scope: dict, question: str) -> str | None:
        """bytes 要 decode；未命中 None。"""
        raise NotImplementedError("实现读取")

    def set(self, scope: dict, question: str, answer: str) -> None:
        """写入时带 ex=ttl_seconds。"""
        raise NotImplementedError("实现写入")


class FixedWindowRateLimiter:
    def __init__(self, redis, limit: int, window_seconds: int):
        raise NotImplementedError("初始化限流")

    def allow(self, tenant_id: str, user_id: str, window: str) -> bool:
        """incr 计数，首次 expire；<= limit 放行。

        redis 异常 -> RuntimeError（失败关闭），不能放开限流。
        """
        raise NotImplementedError("实现限流")
