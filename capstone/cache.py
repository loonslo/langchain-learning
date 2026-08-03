"""租户、权限、模型和知识版本感知的短期答案缓存。"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from cachetools import TTLCache

from . import config as C
from .contracts import Citation
from .permissions import User
from .security import fingerprint


@dataclass(frozen=True)
class CachedAnswer:
    answer: str
    citations: tuple[Citation, ...] = ()


class AnswerCache:
    def __init__(
        self,
        *,
        max_entries: int = C.CACHE_MAX_ENTRIES,
        ttl_seconds: int = C.CACHE_TTL_SECONDS,
    ) -> None:
        self._cache: TTLCache[tuple[str, ...], CachedAnswer | str] = TTLCache(
            maxsize=max_entries,
            ttl=ttl_seconds,
        )
        self._lock = RLock()

    @staticmethod
    def key(
        *,
        tenant_id: str,
        user: User,
        question: str,
        model: str,
        knowledge_version: str,
    ) -> tuple[str, ...]:
        return (
            tenant_id,
            user.user_id,
            user.dept,
            ",".join(sorted(user.roles)),
            model,
            knowledge_version,
            fingerprint(question),
        )

    def get(self, key: tuple[str, ...]) -> CachedAnswer | str | None:
        with self._lock:
            return self._cache.get(key)

    def set(self, key: tuple[str, ...], answer: CachedAnswer | str) -> None:
        with self._lock:
            self._cache[key] = answer

    def invalidate_tenant(self, tenant_id: str) -> None:
        with self._lock:
            for key in [key for key in self._cache if key[0] == tenant_id]:
                self._cache.pop(key, None)


answer_cache = AnswerCache()
