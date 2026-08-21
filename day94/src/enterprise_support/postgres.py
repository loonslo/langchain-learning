"""PostgreSQL 会话仓储：认证身份确定 scope，SQL 永远参数化。"""

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
    role: str
    content: str


class PostgresConversationStore:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def _cursor_for_tenant(self, tenant_id: str) -> Cursor:
        cursor = self.connection.cursor()
        # true = 事务结束即清除，避免连接池把上个租户带给下个请求。
        cursor.execute("SELECT set_config('app.tenant_id', %s, true)", (tenant_id,))
        return cursor

    def append(
        self, *, tenant_id: str, user_id: str, session_id: str, message: ConversationMessage
    ) -> None:
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
        if not 1 <= limit <= 100:
            raise ValueError("limit 必须在 1–100")
        cursor = self._cursor_for_tenant(tenant_id)
        try:
            cursor.execute(
                "SELECT role,content FROM conversation_messages "
                "WHERE user_id=%s AND session_id=%s ORDER BY created_at DESC LIMIT %s",
                (user_id, session_id, limit),
            )
            rows: Iterable[tuple[Any, ...]] = cursor.fetchall()
            return tuple(ConversationMessage(str(role), str(content)) for role, content in reversed(list(rows)))
        finally:
            cursor.close()


def connect_from_dsn(dsn: str) -> Connection:
    """运行时才导入 psycopg，离线单元测试不依赖本地 PostgreSQL。"""
    import psycopg

    return psycopg.connect(dsn)
