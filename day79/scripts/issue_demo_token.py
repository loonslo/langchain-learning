"""为本地 Day79 浏览器演示签发一个短期 JWT；不用于生产。"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", default="demo-shop")
    parser.add_argument("--user", default="demo-user")
    parser.add_argument("--expires", type=int, default=3600)
    args = parser.parse_args()

    backend_root = Path.cwd()
    source_root = backend_root / "src"
    if not (source_root / "customer_support").exists():
        raise SystemExit(
            "请从 .build/day78/customer-support 的 uv 环境运行此脚本，"
            "或将当前目录切换到 Day78 后端根目录。"
        )
    sys.path.insert(0, str(source_root))

    from customer_support.auth import Identity, TokenVerifier

    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 16:
        raise SystemExit("JWT_SECRET 至少需要 16 个字符。")
    token = TokenVerifier(secret).issue(
        Identity(args.tenant, args.user), expires_in=args.expires
    )
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
