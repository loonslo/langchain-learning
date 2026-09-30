"""从仓库根目录运行独立章节，保留现有脚本及其跨章导入。

用法：python tools/run_chapter.py 1.1
      python tools/run_chapter.py 2.1 load_split_formats.py
"""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def resolve_script(chapter: str, filename: str | None = None) -> Path:
    folders = [
        p
        for p in (ROOT / "chapters").glob("part*/*")
        if p.is_dir() and (p.name == chapter or p.name.split("-", 1)[0] == chapter)
    ]
    if len(folders) != 1:
        raise ValueError(f"章节不存在或有歧义：{chapter}")
    folder = folders[0]
    if filename:
        script = (folder / filename).resolve()
        if (
            script.parent != folder.resolve()
            or script.suffix != ".py"
            or not script.is_file()
        ):
            raise ValueError("请指定本章内存在的 Python 文件名")
        return script
    scripts = sorted(p for p in folder.glob("*.py") if not p.name.startswith("test_"))
    if len(scripts) != 1:
        raise ValueError(
            "请指定脚本文件名，可选：" + ", ".join(p.name for p in scripts)
        )
    return scripts[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapter")
    parser.add_argument(
        "arguments", nargs=argparse.REMAINDER, help="可选脚本名，随后是原脚本的参数"
    )
    args = parser.parse_args(argv)
    script_args = list(args.arguments)
    filename = (
        script_args.pop(0) if script_args and script_args[0].endswith(".py") else None
    )
    if script_args and script_args[0] == "--":
        script_args.pop(0)
    try:
        script = resolve_script(args.chapter, filename)
    except ValueError as exc:
        parser.error(str(exc))
    # 仅加入独立练习目录，不加入三条累积项目线的同名业务包。
    lesson_dirs = [
        p
        for p in (ROOT / "chapters").glob("part*/*")
        if p.is_dir()
        and p.parent.name.split("-", 1)[0] in {f"part{i}" for i in range(7)}
    ]
    sys.path[:0] = [str(ROOT), str(script.parent), *(str(p) for p in lesson_dirs)]
    sys.argv = [str(script), *script_args]
    # 示例输入与输出均放在本章目录；即使脚本失败也恢复调用方工作目录。
    original_cwd = Path.cwd()
    try:
        os.chdir(script.parent)
        runpy.run_path(str(script), run_name="__main__")
    finally:
        os.chdir(original_cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
