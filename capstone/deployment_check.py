"""
可执行部署前检查与线上 smoke
==========================================================
“有公网 URL”只是可达，不等于生产就绪。还需最小权限的密钥管理、可重复镜像、
数据许可、迁移/回滚、readiness/liveness、持久化、备份恢复、容量与告警。

默认执行本地仓库检查；传入 --base-url 后再验证线上 /health、/docs，以及未认证
/v1/chat 被拒绝。脚本不打印任何密钥值。
==========================================================
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def _git_check(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def local_preflight() -> list[Check]:
    """检查可确定的本地发布条件；不读取或输出密钥内容。"""
    checks: list[Check] = []
    deploy_doc = ROOT / "capstone" / "DEPLOY.md"
    checks.append(Check("部署文档", deploy_doc.is_file(), str(deploy_doc)))

    dockerfile = ROOT / "Dockerfile"
    docker_text = (
        dockerfile.read_text(encoding="utf-8") if dockerfile.is_file() else ""
    )
    checks.append(
        Check(
            "生产 Dockerfile",
            dockerfile.is_file(),
            str(dockerfile) if dockerfile.is_file() else "只有示例文件不能部署",
        )
    )
    checks.append(
        Check(
            "企业 API 镜像入口",
            "capstone.api_enterprise:app" in docker_text,
            "Dockerfile CMD 必须启动企业 API",
        )
    )
    checks.append(
        Check(
            "Docker 构建上下文排除",
            (ROOT / ".dockerignore").is_file(),
            ".dockerignore 应排除 .env、数据库、报告和本地模型",
        )
    )
    checks.append(
        Check(
            "安装清单",
            (ROOT / "requirements.txt").is_file(),
            "部署必须使用经过锁定和扫描的依赖清单",
        )
    )

    try:
        ignored = _git_check(["check-ignore", "--quiet", ".env"]).returncode == 0
        tracked = _git_check(["ls-files", "--error-unmatch", ".env"]).returncode == 0
    except (OSError, subprocess.TimeoutExpired) as exc:
        checks.append(Check("Git 密钥边界", False, f"无法执行 git 检查：{exc}"))
    else:
        checks.append(Check(".env 已忽略", ignored, "git check-ignore .env"))
        checks.append(
            Check(".env 未被跟踪", not tracked, "已跟踪时必须先轮换泄露密钥")
        )
    return checks


def _request(url: str, *, method: str = "GET", body: bytes | None = None) -> int:
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            return response.status
    except HTTPError as exc:
        return exc.code


def remote_smoke(base_url: str) -> list[Check]:
    """对用户明确提供的部署地址执行无副作用 smoke。"""
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return [Check("线上地址", False, "必须是完整的 http(s) URL")]
    base = base_url.rstrip("/")
    checks: list[Check] = []
    try:
        health = _request(f"{base}/health")
        docs = _request(f"{base}/docs")
        unauthorized = _request(
            f"{base}/v1/chat",
            method="POST",
            body=json.dumps({"question": "smoke"}).encode("utf-8"),
        )
    except (URLError, TimeoutError, OSError) as exc:
        return [Check("线上可达性", False, str(exc))]
    checks.append(Check("/health", health == 200, f"HTTP {health}"))
    checks.append(Check("/docs", docs == 200, f"HTTP {docs}"))
    checks.append(
        Check("未认证请求被拒绝", unauthorized == 401, f"HTTP {unauthorized}")
    )
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", help="已部署服务的根 URL；提供后执行线上 smoke")
    args = parser.parse_args(argv)

    checks = local_preflight()
    if args.base_url:
        checks.extend(remote_smoke(args.base_url))
    for check in checks:
        mark = "OK" if check.passed else "FAIL"
        print(f"[{mark}] {check.name}: {check.detail}")

    failed = [check for check in checks if not check.passed]
    if failed:
        print(f"\n部署检查未通过：{len(failed)} 项。")
        return 1
    if not args.base_url:
        print("\n本地检查通过；尚未执行线上 smoke（使用 --base-url）。")
    else:
        print("\n本地与线上 smoke 均通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
