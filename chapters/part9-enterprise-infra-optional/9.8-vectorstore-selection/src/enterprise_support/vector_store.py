"""向量后端契约与可解释选型；业务层不绑定某个 SDK。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol


class VectorBackend(StrEnum):
    PGVECTOR = "pgvector"
    QDRANT = "qdrant"
    MILVUS = "milvus"


@dataclass(frozen=True)
class VectorRequirements:
    """选型输入：五项约束各自是否成立。"""

    relational_transactions: bool
    filtered_multitenancy: bool
    dedicated_vector_service: bool
    kubernetes_platform: bool
    very_large_scale: bool


def choose_vector_backend(requirements: VectorRequirements) -> VectorBackend:
    """按固定优先级给出起点建议（不是性能结论）：
    1. 规模很大且已有 Kubernetes 平台 → Milvus；
    2. 需要与业务表做事务或 Join，且不要求独立向量服务 → pgvector；
    3. 需要按租户过滤，或要求独立向量服务 → Qdrant；
    4. 都不满足 → pgvector（少引入一个组件）。
    """
    if requirements.very_large_scale and requirements.kubernetes_platform:
        return VectorBackend.MILVUS
    if requirements.relational_transactions and not requirements.dedicated_vector_service:
        return VectorBackend.PGVECTOR
    if requirements.filtered_multitenancy or requirements.dedicated_vector_service:
        return VectorBackend.QDRANT
    return VectorBackend.PGVECTOR


class VectorStore(Protocol):
    """业务层依赖的检索接口；tenant_id 必填，由服务端根据认证身份决定，不接受客户端自报。"""

    def search(self, *, tenant_id: str, vector: list[float], limit: int) -> list[dict[str, Any]]: ...


class QdrantVectorStore:
    """Qdrant client 的薄适配层；tenant filter 是每次查询的必填参数。"""

    def __init__(self, client: Any, *, collection: str = "support_chunks") -> None:
        self.client = client
        self.collection = collection

    @staticmethod
    def tenant_filter(tenant_id: str) -> dict[str, Any]:
        if not tenant_id:
            raise ValueError("tenant_id 不能为空")
        return {"must": [{"key": "tenant_id", "match": {"value": tenant_id}}]}

    def search(self, *, tenant_id: str, vector: list[float], limit: int) -> list[dict[str, Any]]:
        if not 1 <= limit <= 50:
            raise ValueError("limit 必须在 1–50")
        result = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=self.tenant_filter(tenant_id),
            limit=limit,
            with_payload=True,
        )
        points = getattr(result, "points", result)
        return [dict(getattr(point, "payload", {})) for point in points]
