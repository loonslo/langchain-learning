"""展示 Day51–Day78 每日相对上一天的真实文件变更。"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSON_FILES = {"README.md", "workbook.md", "PROJECT_STRUCTURE.md", "deleted_files.txt"}
IGNORED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".pytest-tmp",
    ".ruff_cache",
    ".deepeval",
}


def _is_project_file(path: Path, day_dir: Path) -> bool:
    relative = path.relative_to(day_dir)
    return (
        relative.name not in LESSON_FILES
        and not any(part in IGNORED_PARTS for part in relative.parts)
        and not relative.name.endswith((".pyc", ".pyo"))
    )


def snapshot(day: int) -> dict[str, bytes]:
    """按 materialize_day.py 的规则重建某一天的项目文件。"""

    if day not in range(51, 79):
        raise ValueError("day 必须在 51–78")

    files: dict[str, bytes] = {}
    for number in range(51, day + 1):
        day_dir = ROOT / f"day{number}"
        if not day_dir.is_dir():
            raise FileNotFoundError(f"缺少 {day_dir}")

        manifest = day_dir / "deleted_files.txt"
        if manifest.exists():
            for raw_line in manifest.read_text(encoding="utf-8").splitlines():
                relative = raw_line.strip()
                if relative and not relative.startswith("#"):
                    files.pop(Path(relative).as_posix(), None)

        for source in day_dir.rglob("*"):
            if source.is_file() and _is_project_file(source, day_dir):
                relative = source.relative_to(day_dir).as_posix()
                files[relative] = source.read_bytes()
    return files


def report(day: int) -> str:
    current = snapshot(day)
    previous = snapshot(day - 1) if day > 51 else {}
    added = sorted(set(current) - set(previous))
    modified = sorted(
        path for path in set(current) & set(previous) if current[path] != previous[path]
    )
    removed = sorted(set(previous) - set(current))
    unchanged = sorted(set(current) & set(previous) - set(modified))

    lines = [
        f"# Day{day} 相对 Day{day - 1 if day > 51 else '基线'} 的文件变更",
        "",
        "> 这份报告只比较项目文件，不把 README/workbook 当作产品代码。`修改` 表示旧文件在今天被覆盖了新版本；`继承未改` 表示它仍然参与运行链，但今天没有源码变更。",
        "",
        f"- 新增：{len(added)} 个",
        f"- 修改：{len(modified)} 个",
        f"- 删除：{len(removed)} 个",
        f"- 继承未改：{len(unchanged)} 个",
        "",
    ]

    def add_table(title: str, paths: list[str], empty: str) -> None:
        lines.extend([f"## {title}", "", "| 项目相对路径 |", "|---|"])
        lines.extend(f"| `{path}` |" for path in paths) if paths else lines.append(empty)
        lines.append("")

    add_table("今天新增", added, "无。\n")
    add_table("今天修改的旧文件", modified, "无。\n")
    add_table("今天删除", removed, "无。\n")
    add_table("继续参与主链但今天未改", unchanged, "无。\n")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("day", type=int, choices=range(51, 79))
    args = parser.parse_args(argv)
    print(report(args.day), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
