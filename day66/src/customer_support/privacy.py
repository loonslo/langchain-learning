"""日志前脱敏手机号、邮箱、身份证；不把原始敏感值放进审计字段。"""

import re

PATTERNS = (
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "phone", "[PHONE]"),
    (re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"), "email", "[EMAIL]"),
    (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "id_card", "[ID_CARD]"),
)


def redact(text):
    kinds = []
    for pattern, kind, replacement in PATTERNS:
        text, count = pattern.subn(replacement, text)
        if count:
            kinds.append(kind)
    return text, tuple(kinds)
