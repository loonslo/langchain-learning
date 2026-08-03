"""用仓库事实检查项目是否具备可复现证据。"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str
    required: bool = True


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def audit_repository() -> list[Check]:
    readme_path = ROOT / "capstone" / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    eval_path = ROOT / "capstone" / "data" / "eval_set.json"
    try:
        eval_cases = json.loads(eval_path.read_text(encoding="utf-8"))
        eval_count = len(eval_cases) if isinstance(eval_cases, list) else 0
    except (OSError, json.JSONDecodeError):
        eval_count = 0

    env_tracked = _git("ls-files", "--error-unmatch", ".env").returncode == 0
    env_ignored = _git("check-ignore", "-q", ".env").returncode == 0
    required_paths = (
        "Dockerfile",
        ".dockerignore",
        ".env.example",
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-pgvector.txt",
        "requirements-bedrock.txt",
        "capstone/test_production.py",
        "capstone/contracts.py",
        "capstone/service.py",
        "capstone/approval.py",
        "capstone/load_test.py",
        "capstone/docs/project_brief.md",
        "capstone/docs/day51-78-roadmap.md",
        "capstone/docs/production_readiness.md",
        ".github/workflows/eval-gate.yml",
    )
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    commands = (
        "python -m pip install -r requirements-dev.txt",
        "python -m capstone.main build",
        "python -m capstone.main eval",
        "pytest capstone/test_production.py",
        "python -m capstone.milestones",
        "uvicorn capstone.api_enterprise:app",
    )
    missing_commands = [command for command in commands if command not in readme]
    workflow = ROOT / ".github" / "workflows" / "eval-gate.yml"
    workflow_text = workflow.read_text(encoding="utf-8") if workflow.exists() else ""
    report_exists = (ROOT / "capstone" / "data" / "eval_report.md").exists()
    media = [
        path
        for path in (ROOT / "capstone").rglob("*")
        if path.suffix.lower() in {".gif", ".png", ".jpg", ".jpeg", ".webp"}
    ]

    return [
        Check("README", bool(readme), "capstone/README.md 可读"),
        Check(
            "README 启动命令",
            not missing_commands,
            "齐全" if not missing_commands else f"缺少：{', '.join(missing_commands)}",
        ),
        Check(
            "运行与 CI 文件",
            not missing,
            "齐全" if not missing else f"缺少：{', '.join(missing)}",
        ),
        Check(
            "密钥文件边界",
            env_ignored and not env_tracked,
            f".env ignored={env_ignored}, tracked={env_tracked}",
        ),
        Check(
            "自动评测集",
            eval_count > 0,
            f"{eval_count} 个可解析用例；数量是事实，不包装成 50+",
        ),
        Check(
            "最近评测报告",
            report_exists,
            "存在" if report_exists else "先运行 python -m capstone.main eval",
        ),
        Check(
            "CI 质量门禁",
            "capstone.ci_gate" in workflow_text
            and "capstone/test_production.py" in workflow_text,
            "工作流必须同时覆盖生产边界测试与真实评测门禁",
        ),
        Check(
            "截图/GIF 证据",
            bool(media),
            f"{len(media)} 个媒体文件；没有就不要在简历或 README 声称已有",
            required=False,
        ),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = audit_repository()
    if args.json:
        print(json.dumps([asdict(check) for check in checks], ensure_ascii=False, indent=2))
    else:
        for check in checks:
            icon = "PASS" if check.passed else ("FAIL" if check.required else "WARN")
            print(f"[{icon}] {check.name}: {check.detail}")
    failed = [check for check in checks if check.required and not check.passed]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
