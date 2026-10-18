"""L8 风险建模 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l81", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l81"] = module
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
            "gate": "L8-risk-modeling",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def risk(risk_id="r1", area="rag", impact=4, likelihood=4) -> dict:
    return {"risk_id": risk_id, "area": area, "scenario": "x", "impact": impact, "likelihood": likelihood, "control": "test"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_level():
        expect(core.risk_level(4, 4) == "critical", "16 应 critical")
        expect(core.risk_level(3, 3) == "high", "9 应 high")
        expect(core.risk_level(2, 2) == "medium", "4 应 medium")
        expect(core.risk_level(1, 1) == "low", "1 应 low")
        for impact in (0, 6):
            try:
                core.risk_level(impact, 1)
            except ValueError:
                continue
            raise AssertionError("越界应报错")

    def test_add_validate():
        matrix = core.RiskMatrix()
        matrix.add(risk())
        try:
            matrix.add(risk())
        except ValueError:
            pass
        else:
            raise AssertionError("重复 risk_id 应报错")
        for bad in (risk("r2", area=" "), risk("r3", impact=0), risk("r4", likelihood=6)):
            try:
                core.RiskMatrix().add(bad)
            except ValueError:
                continue
            raise AssertionError(f"非法风险应报错：{bad}")

    def test_priority():
        matrix = core.RiskMatrix()
        matrix.add(risk("b", impact=3, likelihood=3))
        matrix.add(risk("a", impact=4, likelihood=4))
        matrix.add(risk("c", impact=3, likelihood=3))
        expect([r["risk_id"] for r in matrix.prioritized()] == ["a", "b", "c"], f"排序不对：{matrix.prioritized()}")

    def test_uncovered():
        matrix = core.RiskMatrix()
        matrix.add(risk(area="rag"))
        expect(matrix.uncovered_areas({"rag", "agent", "security"}) == {"agent", "security"}, "覆盖不对")

    gate.check("01 风险分级", test_level)
    gate.check("02 入表/校验", test_add_validate)
    gate.check("03 稳定排序", test_priority)
    gate.check("04 空白领域", test_uncovered)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
