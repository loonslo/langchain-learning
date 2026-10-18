"""L8 评测数据工程 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l82", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l82"] = module
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
            "gate": "L8-eval-dataset",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def case(case_id="c1", **overrides) -> dict:
    base = {"case_id": case_id, "question": "q", "expected_keywords": ["k"], "expected_sources": [], "tags": ["rag"], "should_refuse": False, "metadata": {}}
    base.update(overrides)
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_validate():
        expect(core.validate_case(case()) == [], "合法用例不应报错")
        expect(core.validate_case(case(question=" ")), "空问题应报错")
        expect(core.validate_case(case(expected_keywords=[])), "应答题无关键词应报错")
        expect(core.validate_case(case(should_refuse=True, expected_keywords=[])) == [], "拒答无关键词应合法")

    def test_duplicate():
        dataset = core.EvalDataset([case()])
        try:
            dataset.add(case())
        except ValueError:
            return
        raise AssertionError("重复 case_id 应报错")

    def test_validate_dataset():
        dataset = core.EvalDataset([case("a"), case("b", question=" ")])
        errors = dataset.validate()
        expect(list(errors) == ["b"], f"只应报 b：{errors}")

    def test_tag():
        dataset = core.EvalDataset([case("a"), case("b", tags=["agent"])])
        expect([c["case_id"] for c in dataset.by_tag("rag")] == ["a"], "tag 筛选不对")

    def test_roundtrip():
        dataset = core.EvalDataset([case("a")], version="v9")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.json"
            dataset.save(path)
            loaded = core.EvalDataset.load(path)
            expect(loaded.version == "v9" and len(loaded) == 1, "往返失败")
            expect(loaded.by_tag("rag")[0]["case_id"] == "a", "加载内容不对")

    gate.check("01 用例校验", test_validate)
    gate.check("02 重复 id", test_duplicate)
    gate.check("03 整体校验", test_validate_dataset)
    gate.check("04 标签筛选", test_tag)
    gate.check("05 保存/加载", test_roundtrip)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
