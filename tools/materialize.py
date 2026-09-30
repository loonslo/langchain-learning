"""按章节/里程碑顺序重建累积项目状态。

用第一个位置参数选择项目线，以里程碑/章节目录名指定还原目标。
--diff 打印相对上一步的文件变更，不写入还原目录。

用法：
    python tools/materialize.py flagship m3-order-tool-reliability/step2
    python tools/materialize.py quality 8.5-judge-calibration
    python tools/materialize.py enterprise 10.1-mcp-auth-approval --diff
"""

from __future__ import annotations

import argparse
import shutil
from typing import TypedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_ROOT = ROOT / ".build"
LESSON_FILES = {
    "README.md",
    "workbook.md",
    "PROJECT_STRUCTURE.md",
    "PROJECT_README.md",
    "deleted_files.txt",
}
IGNORED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".pytest-tmp",
    ".ruff_cache",
    ".deepeval",
    ".venv",
    "node_modules",
    ".git",
}


class Track(TypedDict):
    target_name: str
    sequence: list[str]


# 每条项目线使用章节或里程碑目录声明累积顺序。
TRACKS: dict[str, Track] = {
    "flagship": {
        "target_name": "customer-support",
        "sequence": [
            "flagship-project/m1-rag-mvp/step1",
            "flagship-project/m1-rag-mvp/step2",
            "flagship-project/m1-rag-mvp/step3",
            "flagship-project/m1-rag-mvp/step4",
            "flagship-project/m2-session-langgraph/step1",
            "flagship-project/m2-session-langgraph/step2",
            "flagship-project/m3-order-tool-reliability/step1",
            "flagship-project/m3-order-tool-reliability/step2",
            "flagship-project/m3-order-tool-reliability/step3",
            "flagship-project/m3-order-tool-reliability/step4",
            "flagship-project/m4-api-identity-security/step1",
            "flagship-project/m4-api-identity-security/step2",
            "flagship-project/m4-api-identity-security/step3",
            "flagship-project/m4-api-identity-security/step4",
            "flagship-project/m5-injection-pii-observability/step1",
            "flagship-project/m5-injection-pii-observability/step2",
            "flagship-project/m5-injection-pii-observability/step3",
            "flagship-project/m5-injection-pii-observability/step4",
            "flagship-project/m6-quality-gate-container/step1",
            "flagship-project/m6-quality-gate-container/step2",
            "flagship-project/m7-capacity-feedback-recovery/step1",
            "flagship-project/m7-capacity-feedback-recovery/step2",
            "flagship-project/m7-capacity-feedback-recovery/step3",
            "flagship-project/m7-capacity-feedback-recovery/step4",
            "flagship-project/m7-capacity-feedback-recovery/step5",
            "flagship-project/m7-capacity-feedback-recovery/step6",
            "flagship-project/m8-evidence-final-frontend/step1",
            "flagship-project/m8-evidence-final-frontend/step2",
            "flagship-project/m8-evidence-final-frontend/step3",
        ],
    },
    "quality": {
        "target_name": "ai-testing",
        "sequence": [
            "chapters/part8-ai-quality-optional/8.1-risk-modeling",
            "chapters/part8-ai-quality-optional/8.2-eval-data-engineering",
            "chapters/part8-ai-quality-optional/8.3-mock-contract-invariant",
            "chapters/part8-ai-quality-optional/8.4-rag-layered-testing",
            "chapters/part8-ai-quality-optional/8.5-judge-calibration",
            "chapters/part8-ai-quality-optional/8.6-agent-trajectory-testing",
            "chapters/part8-ai-quality-optional/8.7-api-sse-e2e",
            "chapters/part8-ai-quality-optional/8.8-security-resilience-perf",
            "chapters/part8-ai-quality-optional/8.9-ci-layered-gate",
            "chapters/part8-ai-quality-optional/8.10-production-feedback-loop",
        ],
    },
    "enterprise": {
        "target_name": "enterprise-support",
        "sequence": [
            "chapters/part9-enterprise-infra-optional/9.1-intent-fewshot",
            "chapters/part9-enterprise-infra-optional/9.2-slot-filling",
            "chapters/part9-enterprise-infra-optional/9.3-stable-json-output",
            "chapters/part9-enterprise-infra-optional/9.4-intent-workflow",
            "chapters/part9-enterprise-infra-optional/9.5-postgres-rls",
            "chapters/part9-enterprise-infra-optional/9.6-readonly-sql-explain",
            "chapters/part9-enterprise-infra-optional/9.7-redis-cache-ratelimit",
            "chapters/part9-enterprise-infra-optional/9.8-vectorstore-selection",
            "chapters/part9-enterprise-infra-optional/9.9-compose-linux-ops",
            "chapters/part9-enterprise-infra-optional/9.10-openai-compatible-provider",
            "chapters/part9-enterprise-infra-optional/9.11-vllm-gpu",
            "chapters/part9-enterprise-infra-optional/9.12-inference-benchmark",
            "chapters/part10-mcp-a2a-optional/10.1-mcp-auth-approval",
            "chapters/part10-mcp-a2a-optional/10.2-a2a-agent-card-task",
            "chapters/part10-mcp-a2a-optional/10.3-a2a-protocol-bindings",
            "chapters/part10-mcp-a2a-optional/10.4-cross-agent-delegation",
        ],
    },
}


def _is_project_file(path: Path, step_dir: Path) -> bool:
    relative = path.relative_to(step_dir)
    return (
        relative.name not in LESSON_FILES
        and relative.name != ".env"
        and not any(part in IGNORED_PARTS for part in relative.parts)
        and not relative.name.endswith((".pyc", ".pyo"))
    )


def resolve_index(track: str, target: str) -> int:
    sequence = TRACKS[track]["sequence"]
    matches = [
        index
        for index, step in enumerate(sequence)
        if step == target or step.endswith("/" + target) or Path(step).name == target
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"步骤 {target!r} 有歧义，请使用完整里程碑/步骤名")
    raise ValueError(f"在 {track} 项目线里找不到步骤 {target!r}；可选值：{sequence}")


def snapshot(track: str, upto_index: int) -> dict[str, bytes]:
    """按顺序叠加 sequence[0..upto_index] 的文件，重建该步骤的累积项目状态。"""
    sequence = TRACKS[track]["sequence"]
    if not 0 <= upto_index < len(sequence):
        raise ValueError(f"步骤索引必须在 0–{len(sequence) - 1}")
    files: dict[str, bytes] = {}
    for step in sequence[: upto_index + 1]:
        step_dir = ROOT / step
        if not step_dir.is_dir():
            raise FileNotFoundError(f"缺少 {step_dir}")

        manifest = step_dir / "deleted_files.txt"
        if manifest.exists():
            for raw_line in manifest.read_text(encoding="utf-8").splitlines():
                relative = raw_line.strip()
                if relative and not relative.startswith("#"):
                    path = Path(relative)
                    if path.is_absolute() or ".." in path.parts or path.drive:
                        raise ValueError(f"非法删除路径：{relative}")
                    prefix = path.as_posix().rstrip("/")
                    for filename in list(files):
                        if filename == prefix or filename.startswith(prefix + "/"):
                            del files[filename]

        for source in step_dir.rglob("*"):
            if source.is_file() and _is_project_file(source, step_dir):
                relative = source.relative_to(step_dir).as_posix()
                files[relative] = source.read_bytes()
    return files


def build_path(track: str, index: int) -> Path:
    step = Path(TRACKS[track]["sequence"][index])
    root = (
        "flagship-project"
        if track == "flagship"
        else step.parts[0] + "/" + step.parts[1]
    )
    return BUILD_ROOT / track / step.relative_to(root) / TRACKS[track]["target_name"]


def materialize(track: str, target: str) -> Path:
    index = resolve_index(track, target)
    files = snapshot(track, index)
    target_dir = build_path(track, index).resolve()
    if (
        not target_dir.is_relative_to(BUILD_ROOT.resolve())
        or target_dir == BUILD_ROOT.resolve()
    ):
        raise RuntimeError("拒绝清理预期目录之外的路径")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)

    for relative, content in files.items():
        destination = (target_dir / relative).resolve()
        if not destination.is_relative_to(target_dir):
            raise ValueError(f"非法输出路径：{relative}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    return target_dir


def diff_report(track: str, target: str) -> str:
    index = resolve_index(track, target)
    sequence = TRACKS[track]["sequence"]
    current = snapshot(track, index)
    previous = snapshot(track, index - 1) if index > 0 else {}
    added = sorted(set(current) - set(previous))
    modified = sorted(
        p for p in set(current) & set(previous) if current[p] != previous[p]
    )
    removed = sorted(set(previous) - set(current))
    unchanged = sorted(set(current) & set(previous) - set(modified))

    step_label = sequence[index]
    prev_label = sequence[index - 1] if index > 0 else "基线"
    lines = [
        f"# {step_label} 相对 {prev_label} 的文件变更",
        "",
        "> 只比较项目文件，不把 README/workbook 当作产品代码。",
        "",
        f"- 新增：{len(added)} 个",
        f"- 修改：{len(modified)} 个",
        f"- 删除：{len(removed)} 个",
        f"- 继承未改：{len(unchanged)} 个",
        "",
    ]

    def add_table(title: str, paths: list[str], empty: str) -> None:
        lines.extend([f"## {title}", "", "| 项目相对路径 |", "|---|"])
        lines.extend(f"| `{path}` |" for path in paths) if paths else lines.append(
            empty
        )
        lines.append("")

    add_table("新增", added, "无。\n")
    add_table("修改的旧文件", modified, "无。\n")
    add_table("删除", removed, "无。\n")
    add_table("继续参与主链但未改", unchanged, "无。\n")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("track", choices=sorted(TRACKS))
    parser.add_argument(
        "target",
        help="里程碑/章节目录名，例如 m3-order-tool-reliability/step2 或 8.5-judge-calibration",
    )
    parser.add_argument(
        "--diff", action="store_true", help="只打印相对上一步的变更报告，不落盘还原"
    )
    args = parser.parse_args(argv)

    try:
        if args.diff:
            print(diff_report(args.track, args.target), end="")
        else:
            print(materialize(args.track, args.target))
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
