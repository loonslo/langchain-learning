"""L3.4 扩展 · Judge 校准 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l85", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l85"] = module
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
            "gate": "L3.4-judge-calibration",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def rows(data: list[tuple[int, float]]) -> list[dict]:
    return [{"case_id": str(i), "gold_label": gold, "judge_score": score} for i, (gold, score) in enumerate(data)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_labels():
        pairs = core.labels_at(rows([(1, 0.9), (0, 0.4)]), 0.5)
        expect(pairs == [(1, 1), (0, 0)], f"标注不对：{pairs}")

    def test_threshold_tie():
        examples = rows([(1, 0.9), (1, 0.75), (0, 0.8), (0, 0.2)])
        report = core.calibrate(examples, (0.5, 0.7, 0.8))
        expect(report["agreement"] == 0.75, f"agreement 不对：{report}")
        expect(report["threshold"] == 0.5, f"并列应取较小阈值：{report}")

    def test_perfect():
        report = core.calibrate(rows([(1, 0.9), (0, 0.1)]))
        expect(report["agreement"] == 1.0, f"应全一致：{report}")
        expect(report["kappa"] == 1.0, f"kappa 应为 1：{report}")

    def test_confusion():
        report = core.calibrate(rows([(1, 0.9), (0, 0.8), (0, 0.1), (1, 0.2)]), (0.5,))
        expect(set(report["confusion"]) == {(0, 0), (0, 1), (1, 0), (1, 1)}, f"混淆矩阵四格不全：{report}")
        expect(report["confusion"][(1, 1)] == 1 and report["confusion"][(0, 1)] == 1, f"计数不对：{report}")

    def test_kappa():
        report = core.calibrate(rows([(1, 0.9), (1, 0.8), (0, 0.7), (0, 0.6)]), (0.5,))
        expect(report["agreement"] == 0.5, f"agreement 不对：{report}")
        expect(report["kappa"] == 0.0, f"kappa 应为 0：{report}")

    def test_empty():
        try:
            core.calibrate([])
        except ValueError:
            return
        raise AssertionError("空样本应抛 ValueError")

    gate.check("01 阈值标注", test_labels)
    gate.check("02 并列取小阈值", test_threshold_tie)
    gate.check("03 完全一致", test_perfect)
    gate.check("04 混淆矩阵", test_confusion)
    gate.check("05 kappa", test_kappa)
    gate.check("06 空样本", test_empty)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
