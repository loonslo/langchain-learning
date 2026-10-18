"""L5.3 扩展 · 向量库选型 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/vector_store.py。实现下面两个函数，然后运行：

    python chapters/part9-enterprise-infra-optional/9.8-vectorstore-selection/gate/gate_check.py
"""

from __future__ import annotations


def choose_vector_backend(requirements: dict) -> str:
    """按固定优先级返回 "milvus" / "pgvector" / "qdrant"。

    输入键：relational_transactions / filtered_multitenancy /
    dedicated_vector_service / kubernetes_platform / very_large_scale。
    优先级：
    1. very_large_scale and kubernetes_platform -> milvus；
    2. relational_transactions and not dedicated_vector_service -> pgvector；
    3. filtered_multitenancy or dedicated_vector_service -> qdrant；
    4. 否则 pgvector。
    """
    raise NotImplementedError("实现选型")


def tenant_filter(tenant_id: str) -> dict:
    """返回 Qdrant 租户过滤条件；空 tenant_id -> ValueError。"""
    raise NotImplementedError("实现租户过滤")
