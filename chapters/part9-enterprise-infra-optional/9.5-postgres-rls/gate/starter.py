"""L5.7 扩展 · Postgres RLS 仓储 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/postgres.py。实现 PostgresConversationStore，然后运行：

    python chapters/part9-enterprise-infra-optional/9.5-postgres-rls/gate/gate_check.py
"""

from __future__ import annotations


class PostgresConversationStore:
    def __init__(self, connection):
        raise NotImplementedError("初始化仓储")

    def append(self, *, tenant_id: str, user_id: str, session_id: str, message: dict) -> None:
        """写一条消息。

        - 先 `SELECT set_config('app.tenant_id', %s, true)` 设置租户；
        - INSERT 参数化，tenant_id 同时写入行；
        - role 只能是 user/assistant，否则 ValueError；
        - 成功 commit；无论成败都 close 游标。
        """
        raise NotImplementedError("实现写入")

    def history(self, *, tenant_id: str, user_id: str, session_id: str, limit: int = 12) -> tuple[dict, ...]:
        """读最近 limit 条，返回旧->新。

        - limit 必须在 1–100，否则 ValueError；
        - 设置租户后再查询；
        - SQL 必须带 tenant_id/user_id/session_id 条件；
        - 读后 commit（结束事务、清除租户设置），并 close 游标。
        """
        raise NotImplementedError("实现历史查询")
