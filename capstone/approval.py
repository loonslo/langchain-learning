"""高风险副作用的持久化审批状态机。"""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from .permissions import User
from .security import redact

ALLOWED_ACTIONS = {"publish_reply"}


class ApprovalWorkflow:
    def __init__(self, database: Path, *, ttl_minutes: int = 30) -> None:
        self.database = database.resolve()
        self.ttl_minutes = ttl_minutes

    def _connect(self) -> sqlite3.Connection:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database, timeout=5)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS approvals(
                approval_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                tenant_id TEXT NOT NULL,
                requester_id TEXT NOT NULL,
                action TEXT NOT NULL,
                request_id TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                draft TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at_utc TEXT NOT NULL,
                expires_at_utc TEXT NOT NULL,
                decided_by TEXT NOT NULL DEFAULT ''
            )"""
        )
        return connection

    def start(
        self,
        *,
        action: str,
        question: str,
        identity: User,
        request_id: str,
        thread_id: str | None,
    ) -> tuple[str, str]:
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"动作不在白名单：{action}")
        normalized_thread = (thread_id or request_id).strip()
        material = (
            f"{identity.tenant_id}\0{identity.user_id}\0{action}\0"
            f"{normalized_thread}\0{request_id}"
        )
        idempotency_key = hashlib.sha256(material.encode()).hexdigest()
        draft = redact(f"待发布回复草稿：{question}")
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=self.ttl_minutes)
        with closing(self._connect()) as connection:
            with connection:
                existing = connection.execute(
                    "SELECT approval_id,draft FROM approvals WHERE idempotency_key=?",
                    (idempotency_key,),
                ).fetchone()
                if existing:
                    return str(existing[0]), str(existing[1])
                approval_id = uuid4().hex
                connection.execute(
                    """INSERT INTO approvals(
                        approval_id,idempotency_key,tenant_id,requester_id,
                        action,request_id,thread_id,draft,status,
                        created_at_utc,expires_at_utc
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        approval_id,
                        idempotency_key,
                        identity.tenant_id,
                        identity.user_id,
                        action,
                        request_id,
                        normalized_thread,
                        draft,
                        "pending",
                        now.isoformat(timespec="seconds"),
                        expires.isoformat(timespec="seconds"),
                    ),
                )
        return approval_id, draft

    def decide(self, approval_id: str, approver: User, *, approved: bool) -> str:
        if not ({"supervisor", "admin"} & approver.roles):
            raise PermissionError("需要 supervisor 或 admin 角色")
        with closing(self._connect()) as connection:
            with connection:
                row = connection.execute(
                    "SELECT tenant_id,draft,status,expires_at_utc FROM approvals "
                    "WHERE approval_id=?",
                    (approval_id,),
                ).fetchone()
                if row is None:
                    raise KeyError("审批不存在")
                tenant_id, draft, status, expires_at = map(str, row)
                if tenant_id != approver.tenant_id:
                    raise PermissionError("审批不属于当前租户")
                if status != "pending":
                    raise RuntimeError("审批已经处理，不能重复使用")
                if datetime.fromisoformat(expires_at) <= datetime.now(UTC):
                    connection.execute(
                        "UPDATE approvals SET status='expired' WHERE approval_id=?",
                        (approval_id,),
                    )
                    raise TimeoutError("审批已过期")
                decision = "approved" if approved else "rejected"
                connection.execute(
                    "UPDATE approvals SET status=?,decided_by=? "
                    "WHERE approval_id=? AND status='pending'",
                    (decision, approver.user_id, approval_id),
                )
        return draft if approved else "审批已拒绝，未执行发布。"
