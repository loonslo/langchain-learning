"""L4.10 流式与人工介入 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l411", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l411"] = module
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
            "gate": "L4.10-hitl",
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

    def test_dangerous():
        for action in ("delete", "send_email", "pay"):
            expect(core.needs_approval(action) is True, f"{action} 应审批")
        expect(core.needs_approval("search") is False, "search 不应审批")

    def test_amount():
        expect(core.needs_approval("transfer", 1001) is True, "超阈值应审批")
        expect(core.needs_approval("transfer", 1000) is False, "等于阈值不应审批")
        expect(core.needs_approval("transfer", None) is False, "无金额不应审批")

    def test_invalid():
        for action, amount in (("", None), ("pay", -1)):
            try:
                core.needs_approval(action, amount)
            except ValueError:
                continue
            raise AssertionError(f"非法输入应报错：{action}, {amount}")

    def test_resolve():
        expect(core.resolve_approval("YES") == "approved", "YES 应 approved")
        expect(core.resolve_approval(" no ") == "cancelled", "no 应 cancelled")
        for bad in ("maybe", ""):
            try:
                core.resolve_approval(bad)
            except ValueError:
                continue
            raise AssertionError("非法审批应报错")

    gate.check("01 危险动作", test_dangerous)
    gate.check("02 金额阈值", test_amount)
    gate.check("03 非法输入", test_invalid)
    gate.check("04 审批归一化", test_resolve)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
