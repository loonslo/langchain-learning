"""PostgreSQL 会话仓储：租户来自认证身份，SQL 一律参数化。

租户隔离有两层：查询自己带 tenant_id 条件（应用层），数据库再按事务内的 app.tenant_id
用 RLS 过滤（数据库层）。两层都保留，任何一层配置出错时另一层仍能挡住越权读取。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol


class Cursor(Protocol):
    def execute(self, query: str, params: tuple[Any, ...] = ()) -> Any: ...

    def fetchall(self) -> list[tuple[Any, ...]]: ...

    def close(self) -> None: ...


class Connection(Protocol):
    def cursor(self) -> Cursor: ...

    def commit(self) -> None: ...


@dataclass(frozen=True)
class ConversationMessage:
    """一条会话消息；role 只能是 user 或 assistant（由表的 CHECK 约束保证）。"""

    role: str
    content: str


class PostgresConversationStore:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def _cursor_for_tenant(self, tenant_id: str) -> Cursor:
        """打开游标并在当前事务里设置租户；调用方必须在同一事务内查询，并在结束时 commit。"""
        cursor = self.connection.cursor()
        # true = 事务结束即清除，避免连接池把上个租户带给下个请求。
        cursor.execute("SELECT set_config('app.tenant_id', %s, true)", (tenant_id,))
        return cursor

    def append(
        self, *, tenant_id: str, user_id: str, session_id: str, message: ConversationMessage
    ) -> None:
        """写入一条消息；tenant_id 同时写入行，并受 RLS 的 WITH CHECK 约束。"""
        cursor = self._cursor_for_tenant(tenant_id)
        try:
            cursor.execute(
                "INSERT INTO conversation_messages(tenant_id,user_id,session_id,role,content) "
                "VALUES(%s,%s,%s,%s,%s)",
                (tenant_id, user_id, session_id, message.role, message.content),
            )
            self.connection.commit()
        finally:
            cursor.close()

    def history(
        self, *, tenant_id: str, user_id: str, session_id: str, limit: int = 12
    ) -> tuple[ConversationMessage, ...]:
        """返回该会话最近 limit 条消息，按时间从旧到新排列。"""
        if not 1 <= limit <= 100:
            raise ValueError("limit 必须在 1–100")
        cursor = self._cursor_for_tenant(tenant_id)
        try:
            cursor.execute(
                "SELECT role,content FROM conversation_messages "
                "WHERE tenant_id=%s AND user_id=%s AND session_id=%s ORDER BY created_at DESC LIMIT %s",
                (tenant_id, user_id, session_id, limit),
            )
            rows: Iterable[tuple[Any, ...]] = cursor.fetchall()
            self.connection.commit()  # 读操作也要结束事务，租户设置才会随之清除
            return tuple(ConversationMessage(str(role), str(content)) for role, content in reversed(list(rows)))
        finally:
            cursor.close()


def connect_from_dsn(dsn: str) -> Connection:
    """运行时才导入 psycopg，离线单元测试不依赖本地 PostgreSQL。"""
    import psycopg

    return psycopg.connect(dsn)
