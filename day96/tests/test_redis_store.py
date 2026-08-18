import pytest

from src.enterprise_support.redis_store import CacheScope, FixedWindowRateLimiter, RedisAnswerCache


class Redis:
    def __init__(self):
        self.data, self.counts, self.ttl = {}, {}, {}

    def get(self, key): return self.data.get(key)
    def set(self, key, value, *, ex): self.data[key] = value; self.ttl[key] = ex
    def delete(self, *keys): return sum(self.data.pop(key, None) is not None for key in keys)
    def incr(self, key): self.counts[key] = self.counts.get(key, 0) + 1; return self.counts[key]
    def expire(self, key, seconds): self.ttl[key] = seconds


def test_cache_key_isolated_by_tenant_and_knowledge_version():
    redis = Redis(); cache = RedisAnswerCache(redis)
    a = CacheScope("a", "v1", "acl1", "model")
    b = CacheScope("b", "v1", "acl1", "model")
    newer = CacheScope("a", "v2", "acl1", "model")
    cache.set(a, "退款 进度", "处理中")
    assert cache.get(a, "退款   进度") == "处理中"
    assert cache.get(b, "退款 进度") is None
    assert cache.get(newer, "退款 进度") is None


def test_rate_limiter_sets_ttl_and_rejects_after_limit():
    redis = Redis(); limiter = FixedWindowRateLimiter(redis, limit=2, window_seconds=60)
    assert limiter.allow(tenant_id="a", user_id="u", window="1")
    assert limiter.allow(tenant_id="a", user_id="u", window="1")
    assert not limiter.allow(tenant_id="a", user_id="u", window="1")


def test_rate_limiter_fails_closed_when_redis_is_down():
    class Down(Redis):
        def incr(self, key): raise ConnectionError("down")
    with pytest.raises(RuntimeError):
        FixedWindowRateLimiter(Down(), limit=1, window_seconds=1).allow(tenant_id="a", user_id="u", window="1")
