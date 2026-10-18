"""L4.6 可观测性 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l49", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l49"] = module
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
            "gate": "L4.6-observability",
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

    def test_record():
        record = core.make_trace_record("plan", {"draft": "x" * 100, "n": 1}, 0.12)
        expect(record["node"] == "plan" and record["ts"] == 0.12, f"基本字段不对：{record}")
        expect(record["update_keys"] == ["draft", "n"], f"keys 不对：{record}")
        expect(record["preview"]["draft"] == "x" * 40, f"预览应截断 40：{record}")
        expect(record["preview"]["n"] == "1", f"预览应转字符串：{record}")

    def test_record_errors():
        for args in (("", {}, 0), ("plan", "bad", 0), ("plan", {}, -1)):
            try:
                core.make_trace_record(*args)
            except ValueError:
                continue
            raise AssertionError(f"非法记录应抛 ValueError：{args}")

    def test_summary():
        records = [
            {"ts": 0.1, "node": "plan", "error": ""},
            {"ts": 0.3, "node": "write", "error": "boom"},
            {"ts": 0.2, "node": "plan", "error": ""},
        ]
        summary = core.summarize_trace(records)
        expect(summary["total"] == 3, f"total 不对：{summary}")
        expect(summary["nodes"] == {"plan": 2, "write": 1}, f"nodes 不对：{summary}")
        expect(summary["slowest"] == "write", f"slowest 不对：{summary}")
        expect(len(summary["errors"]) == 1 and summary["errors"][0]["node"] == "write", f"errors 不对：{summary}")

    def test_empty():
        summary = core.summarize_trace([])
        expect(summary == {"total": 0, "nodes": {}, "slowest": None, "errors": []}, f"空汇总不对：{summary}")

    gate.check("01 轨迹记录", test_record)
    gate.check("02 非法记录", test_record_errors)
    gate.check("03 轨迹汇总", test_summary)
    gate.check("04 空轨迹", test_empty)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
