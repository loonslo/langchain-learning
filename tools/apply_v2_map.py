"""把 v2 路径标签写入章节与旗舰步骤 README。

映射源：docs/course-v2-map.json
用法：
    python tools/apply_v2_map.py --check
    python tools/apply_v2_map.py --apply

只做一件事：在每章 README 的第一个目标/能力条目后加一行
`- **v2 路径**：Lx / 角色（备注）`。重复运行会替换旧行，不会叠加。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "docs" / "course-v2-map.json"

FLAGSHIP = {
    "m1": ("L2.10", "RAG MVP"),
    "m2": ("L4.4", "会话与 LangGraph"),
    "m3": ("L4.4", "工具可靠性"),
    "m4": ("L5.1", "API 与身份"),
    "m5": ("L5.5", "注入/PII/可观测"),
    "m6": ("L5.7", "CI 与容器"),
    "m7": ("L5.8", "容量/反馈/恢复"),
    "m8": ("L6.4", "证据与面试"),
}


def load_map() -> dict[str, dict]:
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def render(meta: dict, suffix: str = "") -> str:
    stage = meta["stage"]
    role = meta["role"]
    note = meta.get("note", "").strip()
    extra = "；".join(part for part in (note, suffix) if part)
    tail = f"（{extra}）" if extra else ""
    return f"- **v2 路径**：{stage} / {role}{tail}"


def chapter_readme(chapter_id: str) -> Path | None:
    matches = list((ROOT / "chapters").glob(f"part*/{chapter_id}-*/README.md"))
    return matches[0] if len(matches) == 1 else None


def upsert(path: Path, line: str, apply: bool) -> str:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    existed = any("**v2 路径**" in old for old in lines)
    if existed:
        kept: list[str] = []
        for old in lines:
            if "**v2 路径**" in old:
                if kept and kept[-1].strip() == "":
                    kept.pop()
                continue
            kept.append(old)
        lines = kept

    bullet_at = next(
        (index for index, old in enumerate(lines) if old.startswith("- **")), None
    )
    if bullet_at is not None:
        updated = lines[: bullet_at + 1] + [line] + lines[bullet_at + 1 :]
    else:
        nav_at = next(
            (
                index
                for index, old in enumerate(lines)
                if old.startswith(("[全书目录]", "[项目目录]", "[返回"))
            ),
            None,
        )
        if nav_at is not None:
            updated = lines[: nav_at + 1] + ["", line] + lines[nav_at + 1 :]
        else:
            updated = lines[:2] + ["", line] + lines[2:]

    new_text = "\n".join(updated) + "\n"
    if new_text == text:
        return "unchanged"
    if apply:
        path.write_text(new_text, encoding="utf-8")
    return "updated" if existed else "inserted"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mapping = load_map()
    apply = args.apply
    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    problems: list[str] = []

    for chapter_id, meta in mapping.items():
        readme = chapter_readme(chapter_id)
        if readme is None:
            problems.append(f"找不到章节 README：{chapter_id}")
            continue
        status = upsert(readme, render(meta), apply)
        counts[status] += 1
        print(f"[{status:9}] {readme.relative_to(ROOT)}  {render(meta)}")

    flagship_root = ROOT / "flagship-project"
    if flagship_root.exists():
        for readme in sorted(flagship_root.glob("m*/step*/README.md")):
            milestone = readme.parent.parent.name
            prefix = milestone.split("-", 1)[0]
            if prefix not in FLAGSHIP:
                problems.append(f"未知里程碑：{milestone}")
                continue
            stage, note = FLAGSHIP[prefix]
            line = render({"stage": stage, "role": "项目", "note": note})
            status = upsert(readme, line, apply)
            counts[status] += 1
            print(f"[{status:9}] {readme.relative_to(ROOT)}  {line}")

    total = sum(counts.values())
    print(
        f"\n合计：{total} 个 README；"
        f"inserted={counts['inserted']} updated={counts['updated']} unchanged={counts['unchanged']}"
    )
    if problems:
        print("问题：", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
