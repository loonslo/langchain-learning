"""写操作幂等：同一 key+payload 只执行一次，不同 payload 明确冲突。"""

import hashlib
import json


class IdempotencyConflict(Exception):
    pass


class IdempotencyStore:
    def __init__(self):
        self.data = {}

    def execute(self, key, payload, operation):
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
