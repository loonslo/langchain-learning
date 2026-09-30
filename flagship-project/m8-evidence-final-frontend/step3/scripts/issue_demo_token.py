"""为里程碑 7.8 的本地浏览器演示签发短期 JWT。"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    repository_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "tools/materialize.py").is_file()
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", default="demo-shop")
    parser.add_argument("--user", default="demo-user")
    parser.add_argument("--expires", type=int, default=3600)
    parser.add_argument(
        "--backend-root",
        type=Path,
        default=repository_root
        / ".build/flagship/m8-evidence-final-frontend/step2/customer-support",
        help="还原后的后端项目目录",
    )
    args = parser.parse_args()

    backend_root = args.backend_root.resolve()
    source_root = backend_root / "src"
    if not (source_root / "customer_support").exists():
        raise SystemExit(
            "请从 .build/flagship/m8-evidence-final-frontend/step2/customer-support 的 uv 环境运行此脚本，"
            "或使用 --backend-root 指定已还原的后端项目。"
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
