"""企业 Copilot 的稳定业务契约；HTTP、CLI、评测和工作流共同使用。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

AssistMode = Literal["auto", "knowledge", "data_query", "action", "memory"]
ResolvedMode = Literal["knowledge", "data_query", "action", "memory"]


@dataclass(frozen=True)
class Citation:
    """只能由实际召回记录构造，不能直接相信模型输出。"""

    source_id: str
    chunk_id: str
    page: int | None = None


@dataclass(frozen=True)
class AssistRequest:
    question: str
    request_id: str
    mode: AssistMode = "auto"
    query_id: str | None = None
    action: str | None = None
    thread_id: str | None = None


@dataclass(frozen=True)
class AssistResult:
    answer: str
    mode: ResolvedMode
    request_id: str
    tenant_id: str
    model: str = ""
    cache_hit: bool = False
    citations: tuple[Citation, ...] = field(default_factory=tuple)
    input_tokens: int = 0
    output_tokens: int = 0
    approval_id: str | None = None
    status: Literal["completed", "pending_approval"] = "completed"


class CapabilityUnavailable(RuntimeError):
    """请求了当前部署未启用的可选能力。"""
