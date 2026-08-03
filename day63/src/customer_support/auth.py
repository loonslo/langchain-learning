"""可信身份来自签名 token，而不是请求正文自报 user_id。"""

from dataclasses import dataclass
from time import time
import jwt


class AuthenticationError(Exception):
    pass


@dataclass(frozen=True)
class Identity:
    tenant_id: str
    user_id: str


class TokenVerifier:
    def __init__(self, secret):
        if len(secret) < 16:
            raise ValueError("secret 太短")
        self.secret = secret

    def issue(self, identity, expires_in=300):
        return jwt.encode(
            {"tenant": identity.tenant_id, "sub": identity.user_id, "exp": int(time()) + expires_in},
            self.secret,
            algorithm="HS256",
        )

    def verify(self, header):
        try:
            if not header.startswith("Bearer "):
                raise AuthenticationError("缺少 Bearer")
            data = jwt.decode(header[7:], self.secret, algorithms=["HS256"])
            return Identity(data["tenant"], data["sub"])
        except (jwt.PyJWTError, KeyError) as exc:
            raise AuthenticationError("token 无效") from exc
