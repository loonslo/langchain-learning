"""L5.7 扩展 · 只读 SQL 护栏 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/sql_guard.py。实现下面三类接口，然后运行：

    python chapters/part9-enterprise-infra-optional/9.6-readonly-sql-explain/gate/gate_check.py
"""

from __future__ import annotations


class SqlPolicyError(ValueError):
    pass


def validate_read_only_sql(sql: str, *, allowed_tables: set[str]) -> str:
    """只读、单语句、无注释、表在白名单、必须显式 LIMIT；返回压缩空白后的 SQL。

    禁止关键字至少含 insert/update/delete/drop/alter/create/grant/revoke/
    copy/call/execute/vacuum/analyze/truncate/into/returning/for/lock。
    """
    raise NotImplementedError("实现只读 SQL 校验")


class QueryCatalog:
    def __init__(self, queries: dict, *, allowed_tables: set[str]):
        raise NotImplementedError("初始化目录")

    def get(self, query_id: str, roles) -> str:
        """未知 id -> SqlPolicyError；角色不匹配 -> PermissionError；取出前再校验只读。"""
        raise NotImplementedError("实现目录取用")


def reject_expensive_plan(plan_json: list[dict], *, max_seq_rows: int = 100_000) -> None:
    """EXPLAIN JSON 中 Seq Scan 的 Plan Rows 超阈值 -> SqlPolicyError；无效结构也报错。"""
    raise NotImplementedError("实现执行计划检查")
