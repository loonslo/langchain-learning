"""L5.7 扩展 · CI 分层门禁 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l89", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l89"] = module
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
            "gate": "L5.7-ci-gate",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def layer(name: str, passed: bool, required: bool = True) -> dict:
    return {"name": name, "passed": passed, "required": required}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_all_pass():
        report = core.evaluate_gate([layer("unit", True), layer("rag", True)])
        expect(report["passed"] is True and report["failed_layers"] == (), f"全通过应放行：{report}")

    def test_required_fail():
        report = core.evaluate_gate([layer("unit", False), layer("rag", True)])
        expect(report["passed"] is False and report["failed_layers"] == ("unit",), f"必需层失败应阻断：{report}")

    def test_optional_fail():
        report = core.evaluate_gate([layer("unit", True), layer("perf", False, required=False)])
        expect(report["passed"] is True and report["failed_layers"] == (), f"可选层失败不应阻断：{report}")

    def test_missing():
        report = core.evaluate_gate([layer("unit", True)], required_layers=("unit", "rag"))
        expect(report["passed"] is False and report["missing_layers"] == ("rag",), f"缺层应阻断：{report}")

    def test_flaky():
        history = {"a": [True, False], "b": [True, True], "c": [False]}
        expect(core.flaky_tests(history) == ("a",), "flaky 检测不对")
        report = core.evaluate_gate([layer("unit", True)], test_history=history)
        expect(report["passed"] is False and report["flaky_tests"] == ("a",), f"flaky 应阻断：{report}")

    def test_empty():
        report = core.evaluate_gate([])
        expect(report["passed"] is True, f"无要求时应放行：{report}")
        report = core.evaluate_gate([], required_layers=("unit",))
        expect(report["passed"] is False and report["missing_layers"] == ("unit",), f"缺必需层应阻断：{report}")

    gate.check("01 全通过", test_all_pass)
    gate.check("02 必需层失败", test_required_fail)
    gate.check("03 可选层失败", test_optional_fail)
    gate.check("04 缺层", test_missing)
    gate.check("05 flaky", test_flaky)
    gate.check("06 空输入", test_empty)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
