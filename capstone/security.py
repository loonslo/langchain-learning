"""输入校验与敏感信息脱敏；不把 Prompt 当作授权机制。"""

from __future__ import annotations

import hashlib
import re

from . import config as C


class SecurityViolation(ValueError):
    """请求在进入检索或模型前被确定性策略拒绝。"""


_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"reveal\s+(the\s+)?(system|developer)\s+prompt", re.I),
    re.compile(r"(忽略|无视).{0,12}(之前|以上|系统).{0,12}(指令|提示)", re.I),
    re.compile(r"(输出|泄露|显示).{0,12}(系统提示词|开发者指令)", re.I),
)
_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")
_CN_ID = re.compile(r"(?<!\d)\d{17}[\dXx](?!\w)")
_SECRET = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|secret)\b\s*[:=]\s*[^\s,;]{8,}"
)


def validate_question(question: str) -> str:
    """规范化用户问题，拒绝控制字符、超长输入和显式越权指令。"""
    normalized = " ".join(question.split())
    if not normalized:
        raise SecurityViolation("问题不能为空")
    if len(normalized) > C.MAX_QUESTION_CHARS:
        raise SecurityViolation(
            f"问题超过最大长度 {C.MAX_QUESTION_CHARS} 个字符"
        )
    if any(ord(char) < 32 and char not in "\t\n\r" for char in question):
        raise SecurityViolation("问题包含非法控制字符")
    if any(pattern.search(normalized) for pattern in _INJECTION_PATTERNS):
        raise SecurityViolation("请求包含试图覆盖系统边界的指令")
    return normalized


def redact(text: str) -> str:
    """对响应、日志或 trace 中的常见敏感信息做确定性脱敏。"""
    value = _EMAIL.sub("[REDACTED_EMAIL]", text)
    value = _PHONE.sub("[REDACTED_PHONE]", value)
    value = _CN_ID.sub("[REDACTED_ID]", value)
    return _SECRET.sub(r"\1=[REDACTED_SECRET]", value)


def fingerprint(text: str) -> str:
    """生成不可逆请求指纹，日志无需保存原问题。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
