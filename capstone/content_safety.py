"""进入统一服务路径的输入/输出审核与无明文审计。"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal
from urllib.error import URLError
from urllib.request import Request, urlopen

from . import config as C
from .security import SecurityViolation, fingerprint, validate_question

LOG = logging.getLogger("capstone.content_safety")
Stage = Literal["input", "output"]


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    code: str


class ContentRejected(SecurityViolation):
    def __init__(self, stage: Stage, code: str) -> None:
        super().__init__(f"{stage} 内容未通过安全审核")
        self.stage = stage
        self.code = code


class SafetyUnavailable(RuntimeError):
    """外部审核器不可用时失败关闭，调用方返回暂时不可用。"""


Moderator = Callable[[str, Stage], SafetyDecision]


def _terms() -> tuple[str, ...]:
    raw = os.getenv("CONTENT_SAFETY_BLOCKLIST", "").strip() or (
        "违禁示例词A,违禁示例词B,炸药配方,赌博网站"
    )
    return tuple(term.strip().casefold() for term in raw.split(",") if term.strip())


def local_moderate(text: str, stage: Stage) -> SafetyDecision:
    if any(term in text.casefold() for term in _terms()):
        return SafetyDecision(False, f"{stage}_local_policy")
    if stage == "input":
        try:
            validate_question(text)
        except SecurityViolation:
            return SafetyDecision(False, "input_security_boundary")
    return SafetyDecision(True, "ok")


class HttpModerator:
    """最小 HTTP 适配器；外部服务返回 `{allowed, code}`。"""

    def __init__(self, url: str, *, timeout_seconds: float = 3) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds

    def __call__(self, text: str, stage: Stage) -> SafetyDecision:
        headers = {"Content-Type": "application/json"}
        api_key = os.getenv("CONTENT_SAFETY_API_KEY", "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = Request(
            self.url,
            data=json.dumps({"text": text, "stage": stage}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, TimeoutError, URLError, json.JSONDecodeError) as exc:
            raise SafetyUnavailable("外部内容审核器不可用") from exc
        if not isinstance(payload, dict) or type(payload.get("allowed")) is not bool:
            raise SafetyUnavailable("外部内容审核器响应格式无效")
        return SafetyDecision(
            payload["allowed"], str(payload.get("code", "external_policy"))
        )


class ContentSafetyGateway:
    def __init__(
        self,
        external: Moderator | None = None,
        *,
        require_external: bool = False,
    ) -> None:
        self.external = external
        self.require_external = require_external

    @staticmethod
    def _audit(text: str, stage: Stage, decision: SafetyDecision, request_id: str):
        LOG.info(
            "content_safety_audit %s",
            json.dumps(
                {
                    "request_id": request_id,
                    "stage": stage,
                    "allowed": decision.allowed,
                    "code": decision.code,
                    "content_fingerprint": fingerprint(text),
                },
                ensure_ascii=False,
            ),
        )

    def _check(self, text: str, stage: Stage, request_id: str) -> None:
        decision = local_moderate(text, stage)
        if decision.allowed and self.external is not None:
            try:
                decision = self.external(text, stage)
            except SafetyUnavailable:
                raise
            except Exception as exc:
                raise SafetyUnavailable("外部内容审核器不可用") from exc
            if not isinstance(decision, SafetyDecision):
                raise SafetyUnavailable("外部内容审核器响应类型无效")
        elif decision.allowed and self.require_external:
            raise SafetyUnavailable("生产环境缺少外部内容审核器")
        self._audit(text, stage, decision, request_id)
        if not decision.allowed:
            raise ContentRejected(stage, decision.code)

    def check_input(self, text: str, *, request_id: str) -> None:
        self._check(text, "input", request_id)

    def check_output(self, text: str, *, request_id: str) -> None:
        self._check(text, "output", request_id)


def configuration_errors() -> list[str]:
    if C.APP_ENV != "production":
        return []
    if not os.getenv("CONTENT_SAFETY_URL", "").strip():
        return ["生产环境必须配置 CONTENT_SAFETY_URL 或注入等价审核器"]
    return []


def from_environment() -> ContentSafetyGateway:
    url = os.getenv("CONTENT_SAFETY_URL", "").strip()
    external = HttpModerator(url) if url else None
    return ContentSafetyGateway(
        external,
        require_external=C.APP_ENV == "production",
    )
