"""L3.5 Ragas 与指标口径 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l35", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l35"] = module
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
            "gate": "L3.5-ragas",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


BASE = [
    {"id": "f01", "question": "RAG 是什么", "reference": "检索增强生成", "keywords": ["检索"], "type": "fact", "should_refuse": False},
    {"id": "m01", "question": "RAG 和向量库", "reference": "向量库是核心组件", "keywords": ["向量"], "type": "multi_hop", "should_refuse": False},
]
EXTRA = [
    {"id": "r01", "question": "作者是谁", "reference": "文档未提及", "keywords": [], "type": "refuse", "should_refuse": True},
    {"id": "c01", "question": "依据在哪", "reference": "来自向量库段落", "keywords": [], "type": "citation", "should_refuse": False},
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def ask(case: dict) -> dict:
        return {"answer": f"答案：{case['reference']}", "contexts": ["片段1", "片段2"]}

    def test_merge():
        base = copy.deepcopy(BASE)
        extra = copy.deepcopy(EXTRA)
        rows = core.merge_sets(base, extra)
        expect([row["id"] for row in rows] == ["f01", "m01", "r01", "c01"], f"合并顺序不对：{rows}")
        expect(base == BASE and extra == EXTRA, "不应修改输入")

    def test_merge_duplicate():
        try:
            core.merge_sets(BASE, [BASE[0]])
        except ValueError:
            return
        raise AssertionError("重复 ID 应抛 ValueError")

    def test_merge_missing():
        try:
            core.merge_sets(BASE, [{"id": "x"}])
        except ValueError:
            return
        raise AssertionError("缺 type 应抛 ValueError")

    def test_validate():
        report = core.validate_full_set(BASE + EXTRA)
        expect(report["ok"] is True, f"合法全集应通过：{report}")
        expect(report["refuse_count"] == 1, f"refuse_count 不对：{report}")
        expect(report["type_counts"] == {"fact": 1, "multi_hop": 1, "refuse": 1, "citation": 1}, f"type_counts 不对：{report}")

    def test_validate_bad():
        bad_refuse = {"id": "r02", "question": "q", "reference": "x", "keywords": ["x"], "type": "refuse", "should_refuse": True}
        for rows in ([], BASE + [bad_refuse]):
            report = core.validate_full_set(rows)
            expect(report["ok"] is False and report["errors"], f"应报错：{report}")

    def test_ragas_rows():
        rows = core.build_ragas_rows(BASE + EXTRA, ask)
        expect(rows["question"] == ["RAG 是什么", "RAG 和向量库", "依据在哪"], f"应跳过拒答：{rows}")
        expect(rows["contexts"][0] == ["片段1", "片段2"], f"contexts 不对：{rows}")
        expect(rows["ground_truth"][0] == "检索增强生成", f"ground_truth 不对：{rows}")

    def test_ragas_errors():
        for fn in (lambda case: {"answer": "x"}, lambda case: {"contexts": []}, lambda case: {"answer": 1, "contexts": []}):
            try:
                core.build_ragas_rows(BASE, fn)
            except ValueError:
                continue
            raise AssertionError("非法 ask_fn 结果应抛 ValueError")

    def test_no_mutation():
        cases = copy.deepcopy(BASE + EXTRA)
        original = copy.deepcopy(cases)
        core.build_ragas_rows(cases, ask)
        expect(cases == original, "不应修改 cases")

    gate.check("01 合并顺序与副本", test_merge)
    gate.check("02 拒绝重复 ID", test_merge_duplicate)
    gate.check("03 拒绝缺字段", test_merge_missing)
    gate.check("04 全集校验与计数", test_validate)
    gate.check("05 空集/拒答关键词错误", test_validate_bad)
    gate.check("06 RAGAS 四列", test_ragas_rows)
    gate.check("07 ask_fn 结果校验", test_ragas_errors)
    gate.check("08 不修改输入", test_no_mutation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
