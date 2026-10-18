"""检查课程 Markdown 的相对链接是否存在。

用法：
    python tools/check_course_links.py
    python tools/check_course_links.py --root chapters --root flagship-project

只检查本地相对路径；跳过 http(s)、mailto、纯锚点和代码块里的示例。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def markdown_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".md":
            files.append(root)
        elif root.is_dir():
            files.extend(sorted(root.rglob("*.md")))
    return files


def check_file(path: Path) -> list[tuple[int, str, str]]:
    problems: list[tuple[int, str, str]] = []
    in_fence = False
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for raw in LINK.findall(line):
            target = raw.strip().strip("<>").split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if target.startswith("/") or "://" in target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                problems.append((lineno, raw, str(resolved)))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        action="append",
        default=None,
        help="要检查的根目录或文件，可重复；默认 chapters、flagship-project、docs 和根 README",
    )
    args = parser.parse_args(argv)
    if args.root:
        roots = [Path(item) if Path(item).is_absolute() else ROOT / item for item in args.root]
    else:
        roots = [
            ROOT / "chapters",
            ROOT / "flagship-project",
            ROOT / "docs",
            ROOT / "README.md",
            ROOT / "TASKS.md",
            ROOT / "PROJECT_STATUS.md",
        ]

    files = markdown_files(roots)
    total = 0
    for path in files:
        problems = check_file(path)
        if not problems:
            continue
        total += len(problems)
        print(f"\n{path.relative_to(ROOT)}")
        for lineno, raw, resolved in problems:
            print(f"  L{lineno}: {raw}")
            print(f"        -> {resolved}")
    print(f"\n检查 {len(files)} 个 Markdown 文件；断链 {total} 个。")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
