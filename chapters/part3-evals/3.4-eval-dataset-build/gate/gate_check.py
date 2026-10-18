"""L3.2 评测集建设 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l34b", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l34b"] = module
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
            "gate": "L3.2-dataset-build",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def row(**overrides) -> dict:
    data = {
        "id": "f01",
        "question": "RAG 是什么",
        "reference": "检索增强生成",
        "keywords": ["检索", "生成"],
        "expect_source": "test_doc.txt",
        "type": "fact",
        "should_refuse": False,
    }
    data.update(overrides)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_valid():
        rows = [row(), row(id="m01", type="multi_hop"), row(id="r01", type="refuse", keywords=[], should_refuse=True)]
        report = core.validate_dataset(rows)
        expect(report["ok"] is True, f"合法评测集应通过：{report}")
        expect(report["type_counts"] == {"fact": 1, "multi_hop": 1, "refuse": 1}, f"计数不对：{report}")

    def test_empty():
        report = core.validate_dataset([])
        expect(report["ok"] is False and any("empty" in e for e in report["errors"]), f"空集应失败：{report}")

    def test_missing_field():
        bad = row()
        bad.pop("reference")
        report = core.validate_dataset([bad])
        expect(report["ok"] is False and any("f01" in e for e in report["errors"]), f"缺字段应报错：{report}")

    def test_duplicate_id():
        report = core.validate_dataset([row(), row()])
        expect(report["ok"] is False and any("duplicate" in e.lower() or "重复" in e for e in report["errors"]), f"重复 ID 应报错：{report}")

    def test_bad_types():
        cases = [
            row(type="unknown"),
            row(keywords="检索"),
            row(should_refuse="no"),
            row(question="   "),
        ]
        for case in cases:
            report = core.validate_dataset([case])
            expect(report["ok"] is False and report["errors"], f"非法字段应报错：{case}")

    def test_collects_multiple_errors():
        report = core.validate_dataset([row(type="unknown", keywords="bad")])
        expect(len(report["errors"]) >= 2, f"应收集多条错误：{report}")

    def test_coverage():
        rows = [row(), row(id="m01", type="multi_hop")]
        report = core.coverage(rows)
        expect(report["total"] == 2, f"total 不对：{report}")
        expect(report["types"] == {"fact": 1, "multi_hop": 1}, f"types 不对：{report}")
        expect(set(report["missing_types"]) == {"refuse", "citation"}, f"missing 不对：{report}")

    gate.check("01 合法评测集", test_valid)
    gate.check("02 空评测集", test_empty)
    gate.check("03 缺字段", test_missing_field)
    gate.check("04 重复 ID", test_duplicate_id)
    gate.check("05 非法字段类型", test_bad_types)
    gate.check("06 收集多条错误", test_collects_multiple_errors)
    gate.check("07 题型覆盖", test_coverage)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
