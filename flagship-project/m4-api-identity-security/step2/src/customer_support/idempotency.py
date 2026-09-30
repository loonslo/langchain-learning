"""写操作幂等：同一 key+payload 只执行一次，不同 payload 明确冲突。"""

import hashlib
import json


class IdempotencyConflict(Exception):
    """同一个幂等键被用于不同的请求内容。"""


class IdempotencyStore:
    def __init__(self):
        self.data = {}

    def execute(self, key, payload, operation):
        """同一 key + 同一 payload 只执行一次，重复调用直接返回第一次的结果；同一 key 换了 payload 抛 IdempotencyConflict。
        进程内字典：不跨进程、不线程安全，重启后丢失。
        """
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        if key in self.data:
            old, value = self.data[key]
            if old != fingerprint:
                raise IdempotencyConflict(key)
            return value
        value = operation()
        self.data[key] = (fingerprint, value)
        return value
