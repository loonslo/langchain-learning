"""数据库 Agent 的最小安全底线：目录优先，动态 SQL 必须只读且可估算。"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


_WORDS = re.compile(r"\b[a-z_]+\b", re.I)
_TABLES = re.compile(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", re.I)
_FORBIDDEN = {
    "insert", "update", "delete", "drop", "alter", "create", "grant", "revoke",
    "copy", "call", "execute", "vacuum", "analyze", "truncate", "into", "returning",
    "pg_sleep", "for", "lock",
}


class SqlPolicyError(ValueError):
    pass


def validate_read_only_sql(sql: str, *, allowed_tables: set[str]) -> str:
    compact = " ".join(sql.strip().split())
    lowered = compact.lower()
    if not (lowered.startswith("select ") or lowered.startswith("with ")):
        raise SqlPolicyError("只允许 SELECT 或只读 WITH 查询")
    if ";" in compact or "--" in compact or "/*" in compact:
        raise SqlPolicyError("不允许多语句或 SQL 注释")
    words = set(_WORDS.findall(lowered))
    if words & _FORBIDDEN:
        raise SqlPolicyError(f"出现禁止关键字：{sorted(words & _FORBIDDEN)}")
    tables = set(_TABLES.findall(lowered))
    if not tables or not tables <= allowed_tables:
        raise SqlPolicyError("查询表不在允许目录")
    if " limit " not in f" {lowered} ":
        raise SqlPolicyError("查询必须显式 LIMIT")
    return compact


@dataclass(frozen=True)
class CatalogQuery:
    sql: str
    allowed_roles: frozenset[str]


class QueryCatalog:
    def __init__(self, queries: Mapping[str, CatalogQuery], *, allowed_tables: set[str]) -> None:
        self.queries = dict(queries)
        self.allowed_tables = allowed_tables

    def get(self, query_id: str, roles: Iterable[str]) -> str:
        query = self.queries.get(query_id)
        if query is None:
            raise SqlPolicyError("未知 query_id")
        if not query.allowed_roles.intersection(roles):
            raise PermissionError("当前身份无权执行此查询")
        return validate_read_only_sql(query.sql, allowed_tables=self.allowed_tables)


def _nodes(plan: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    yield plan
    for child in plan.get("Plans", []) or []:
        if isinstance(child, Mapping):
            yield from _nodes(child)


def reject_expensive_plan(plan_json: list[Mapping[str, Any]], *, max_seq_rows: int = 100_000) -> None:
    """接收 EXPLAIN (FORMAT JSON) 结果；超过阈值顺扫必须先优化查询/索引。"""
    if not plan_json or not isinstance(plan_json[0].get("Plan"), Mapping):
        raise SqlPolicyError("无效 EXPLAIN JSON")
    for node in _nodes(plan_json[0]["Plan"]):
        if node.get("Node Type") == "Seq Scan" and int(node.get("Plan Rows", 0)) > max_seq_rows:
            raise SqlPolicyError("执行计划包含超阈值顺序扫描")
