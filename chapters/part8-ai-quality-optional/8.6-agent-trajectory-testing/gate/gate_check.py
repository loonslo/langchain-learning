"""L4.11 扩展 · Agent 轨迹测试 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l86", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l86"] = module
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
            "gate": "L4.11-trajectory-testing",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


POLICY = {"allowed_tools": {"search", "send_email"}, "max_steps": 3, "write_tools": {"send_email"}}


def step(n: int, action: str, tool: str | None = None, approved: bool = False) -> dict:
    return {"step": n, "action": action, "tool": tool, "approved": approved}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_valid():
        expect(core.validate_trajectory([step(1, "tool", "search"), step(2, "respond")], POLICY) == [], "合规轨迹不应报错")

    def test_unknown_tool():
        issues = core.validate_trajectory([step(1, "tool", "delete_db")], POLICY)
        expect(any("工具未授权" in i for i in issues), f"应报未授权：{issues}")

    def test_write_unapproved():
        issues = core.validate_trajectory([step(1, "tool", "send_email")], POLICY)
        expect(any("审批" in i for i in issues), f"应报缺审批：{issues}")
        expect(core.validate_trajectory([step(1, "tool", "send_email", True), step(2, "respond")], POLICY) == [], "已审批应合规")

    def test_step_gap():
        issues = core.validate_trajectory([step(1, "tool", "search"), step(3, "respond")], POLICY)
        expect(any("编号不连续" in i for i in issues), f"应报编号：{issues}")

    def test_max_steps():
        steps = [step(i, "tool", "search") for i in range(1, 5)]
        issues = core.validate_trajectory(steps, POLICY)
        expect(any("最大步骤数" in i for i in issues), f"应报超步数：{issues}")

    def test_unknown_action():
        issues = core.validate_trajectory([step(1, "think")], POLICY)
        expect(any("未知动作" in i for i in issues), f"应报未知动作：{issues}")

    gate.check("01 合规轨迹", test_valid)
    gate.check("02 工具白名单", test_unknown_tool)
    gate.check("03 写工具审批", test_write_unapproved)
    gate.check("04 编号连续", test_step_gap)
    gate.check("05 最大步数", test_max_steps)
    gate.check("06 未知动作", test_unknown_action)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
