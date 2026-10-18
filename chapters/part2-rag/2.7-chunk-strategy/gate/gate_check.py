"""L2.4 切分策略 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l27", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l27"] = module
    spec.loader.exec_module(module)
    return module


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class Gate:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def check(self, name: str, fn) -> None:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            self.rows.append({"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
        else:
            self.rows.append({"name": name, "ok": True, "error": ""})

    def report(self, module_path: Path) -> int:
        passed = sum(row["ok"] for row in self.rows)
        total = len(self.rows)
        for row in self.rows:
            mark = "PASS" if row["ok"] else "FAIL"
            print(f"[{mark}] {row['name']}" + ("" if row["ok"] else f"  <- {row['error']}"))
        print(f"\n{passed}/{total} passed")
        if passed != total:
            print("gate 未通过：先修 FAIL 项，不要打开参考实现。")
        out = {
            "gate": "L2.4-chunk-strategy",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_empty_and_bad():
        expect(core.split_preserving_boundaries("   ", 10) == [], "空文本应返回 []")
        for size in (0, -1):
            try:
                core.split_preserving_boundaries("abc", size)
            except ValueError:
                continue
            raise AssertionError("max_chars<=0 应抛 ValueError")

    def test_short_text():
        rows = core.split_preserving_boundaries("第一段。", 20)
        expect(rows == ["第一段。"], f"短文本应整段保留：{rows}")

    def test_paragraph_boundary():
        rows = core.split_preserving_boundaries("第一段。\n\n第二段。", 5)
        expect(rows == ["第一段。", "第二段。"], f"应按段落切：{rows}")

    def test_sentence_boundary():
        rows = core.split_preserving_boundaries("句子一。句子二。句子三。", 6)
        expect(rows == ["句子一。", "句子二。", "句子三。"], f"应按句子切：{rows}")
        expect(all(len(row) <= 6 for row in rows), f"片段超长：{rows}")

    def test_hard_cut():
        rows = core.split_preserving_boundaries("abcdefghij", 3)
        expect(rows == ["abc", "def", "ghi", "j"], f"单句超长应硬切：{rows}")

    def test_no_empty_and_limit():
        text = "第一句。第二句。\n\n第三段很长很长。\n\n短。"
        rows = core.split_preserving_boundaries(text, 7)
        expect(all(row.strip() for row in rows), f"不应有空片段：{rows}")
        expect(all(len(row) <= 7 for row in rows), f"片段超长：{rows}")
        expect("".join(rows).replace("\n", "") != "", "输出不应为空")

    def test_stats():
        stats = core.chunk_stats(["abc", "de", "", "fghi"])
        expect(stats["count"] == 4, f"count 不对：{stats}")
        expect(stats["empty_count"] == 1, f"empty_count 不对：{stats}")
        expect(stats["max_len"] == 4, f"max_len 不对：{stats}")
        expect(abs(stats["avg_len"] - 2.25) < 1e-9, f"avg_len 不对：{stats}")
        expect(core.chunk_stats([]) == {"count": 0, "avg_len": 0, "max_len": 0, "empty_count": 0}, "空统计不对")

    gate.check("01 空文本与非法 max_chars", test_empty_and_bad)
    gate.check("02 短文本不切", test_short_text)
    gate.check("03 优先按段落", test_paragraph_boundary)
    gate.check("04 段落超长按句子", test_sentence_boundary)
    gate.check("05 单句超长硬切", test_hard_cut)
    gate.check("06 无空片段且不超长", test_no_empty_and_limit)
    gate.check("07 切分统计", test_stats)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
