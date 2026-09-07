"""兼容入口：适配器的唯一实现已经合并到 ``production_graph.py``。

历史教学代码和旧测试仍然可能写着 ``from day31_40.adapters import ...``，
所以暂时保留这个很薄的转发模块。它不再存放第二套实现，新的学习和业务代码
应优先直接阅读/导入 ``production_graph.py``。
"""

from __future__ import annotations

from .production_graph import (
    EvidenceAdapter,
    MultiServerMcpAdapter,
    PermanentToolError,
    ResilientAdapter,
    SafeSqlAdapter,
    TavilySearchAdapter,
    TransientToolError,
    call_with_timeout,
    init_car_database,
    upsert_candidate_car,
    upsert_family_profile,
    validate_readonly_sql,
)

__all__ = [
    "EvidenceAdapter",
    "MultiServerMcpAdapter",
    "PermanentToolError",
    "ResilientAdapter",
    "SafeSqlAdapter",
    "TavilySearchAdapter",
    "TransientToolError",
    "call_with_timeout",
    "init_car_database",
    "upsert_candidate_car",
    "upsert_family_profile",
    "validate_readonly_sql",
]
