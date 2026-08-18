"""按 Day90..Day105 的每日变更重建企业客服进阶项目。"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BUILD_ROOT = ROOT / ".build"
LESSON_FILES = {"README.md", "workbook.md", "PROJECT_README.md", "deleted_files.txt"}
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".pytest-tmp", ".ruff_cache"}


def _is_project_file(path: Path, day_dir: Path) -> bool:
    relative = path.relative_to(day_dir)
    return (
        relative.name not in LESSON_FILES
        and not any(part in IGNORED_PARTS for part in relative.parts)
        and not relative.name.endswith((".pyc", ".pyo"))
    )


def materialize(day: int) -> Path:
    if day not in range(90, 106):
        raise ValueError("day 必须在 90–105")

    target = (BUILD_ROOT / f"day{day}" / "enterprise-support").resolve()
    expected_parent = (BUILD_ROOT / f"day{day}").resolve()
    if target.parent != expected_parent:
        raise RuntimeError("拒绝清理预期目录之外的路径")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    for number in range(90, day + 1):
        day_dir = ROOT / f"day{number}"
        if not day_dir.exists():
            raise FileNotFoundError(f"缺少 day{number} 目录")
        for source in day_dir.rglob("*"):
            if not source.is_file() or not _is_project_file(source, day_dir):
                continue
            relative = source.relative_to(day_dir)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("day", type=int, choices=range(90, 106))
    args = parser.parse_args(argv)
    print(materialize(args.day))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
