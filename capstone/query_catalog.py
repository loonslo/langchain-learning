"""受控业务查询：模型只能选择 query_id，不能生成可执行 SQL。"""

from __future__ import annotations

import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .permissions import User


@dataclass(frozen=True)
class QueryDefinition:
    sql: str
    max_rows: int


QUERY_CATALOG = {
    "my_conversations": QueryDefinition(
        "SELECT user_id, question FROM conversations "
        "WHERE tenant_id=? AND user_id=? ORDER BY id DESC LIMIT ?",
        10,
    )
}


class CatalogQueryTool:
    def __init__(self, database: Path, *, timeout_seconds: float = 0.2) -> None:
        self.database = database.resolve()
        self.timeout_seconds = timeout_seconds

    def _connect(self) -> sqlite3.Connection:
        if not self.database.is_file():
            raise FileNotFoundError(f"业务数据库不存在：{self.database}")
        connection = sqlite3.connect(
            self.database.as_uri() + "?mode=ro",
            uri=True,
        )
        connection.execute("PRAGMA query_only=ON")
        return connection

    def execute(self, query_id: str, identity: User) -> list[tuple[object, ...]]:
        try:
            definition = QUERY_CATALOG[query_id]
        except KeyError as exc:
            raise ValueError(f"未知 query_id：{query_id}") from exc
        started = time.monotonic()
        with closing(self._connect()) as connection:
            connection.set_progress_handler(
                lambda: int(time.monotonic() - started > self.timeout_seconds),
                1_000,
            )
            try:
                rows = connection.execute(
                    definition.sql,
                    (
                        identity.tenant_id,
                        identity.user_id,
                        definition.max_rows,
                    ),
                ).fetchall()
            finally:
                connection.set_progress_handler(None, 0)
        if len(rows) > definition.max_rows:
            raise RuntimeError("查询结果超过目录定义的行数上限")
        return rows
