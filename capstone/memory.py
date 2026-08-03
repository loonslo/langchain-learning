"""显式同意、可查看和可删除的租户隔离回复偏好。"""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock

from .permissions import User

_REMEMBER = re.compile(r"^请记住我的回复语言为(中文|英文)$")
_SHOW = "查看你记住了什么"
_FORGET = "删除我的偏好"


class PreferenceMemory:
    """只保存受控偏好，不从普通对话静默抽取长期记忆。"""

    def __init__(self, database: Path) -> None:
        self.database = database.resolve()
        self._write_lock = RLock()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.database, timeout=5)) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS user_preferences(
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    response_language TEXT NOT NULL,
                    consent TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    PRIMARY KEY(tenant_id, user_id)
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database, timeout=5)

    def handles(self, message: str) -> bool:
        normalized = " ".join(message.split())
        return bool(_REMEMBER.fullmatch(normalized)) or normalized in {
            _SHOW,
            _FORGET,
        }

    def context(self, identity: User) -> str:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT response_language FROM user_preferences "
                "WHERE tenant_id=? AND user_id=?",
                (identity.tenant_id, identity.user_id),
            ).fetchone()
        return f"回复语言={row[0]}" if row else ""

    def apply(self, message: str, identity: User) -> str:
        normalized = " ".join(message.split())
        if normalized == _SHOW:
            value = self.context(identity)
            return f"当前显式偏好：{value}" if value else "当前没有保存偏好。"
        if normalized == _FORGET:
            with self._write_lock, closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        "DELETE FROM user_preferences WHERE tenant_id=? AND user_id=?",
                        (identity.tenant_id, identity.user_id),
                    )
            return "已删除你的回复偏好。"
        match = _REMEMBER.fullmatch(normalized)
        if match is None:
            raise ValueError("只允许显式设置、查看或删除受控回复偏好")
        language = match.group(1)
        with self._write_lock, closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """INSERT INTO user_preferences(
                        tenant_id,user_id,response_language,consent,updated_at_utc
                    ) VALUES(?,?,?,?,?)
                    ON CONFLICT(tenant_id,user_id) DO UPDATE SET
                        response_language=excluded.response_language,
                        consent=excluded.consent,
                        updated_at_utc=excluded.updated_at_utc""",
                    (
                        identity.tenant_id,
                        identity.user_id,
                        language,
                        "explicit_command",
                        datetime.now(UTC).isoformat(timespec="seconds"),
                    ),
                )
        return f"已记住：回复语言={language}。"
