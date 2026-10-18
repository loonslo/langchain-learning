"""L1.3 结构化输出 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA = {"summary": str, "issues": list, "score": int}


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l13", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l13"] = module
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
            "gate": "L1.3-structured-output",
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

    def test_plain_json():
        text = '{"summary": "ok", "issues": [], "score": 8}'
        data = core.parse_model_json(text, SCHEMA)
        expect(data["summary"] == "ok" and data["score"] == 8, f"解析不对：{data}")

    def test_fenced_and_prose():
        text = '结果如下：\n```json\n{"summary": "ok", "issues": ["x"], "score": 7}\n```\n以上。'
        data = core.parse_model_json(text, SCHEMA)
        expect(data["issues"] == ["x"], f"围栏/说明文字解析不对：{data}")

    def test_missing_field():
        text = '{"summary": "ok", "score": 8}'
        try:
            core.parse_model_json(text, SCHEMA)
        except core.SchemaError:
            return
        raise AssertionError("缺字段应抛 SchemaError")

    def test_wrong_type():
        for text in (
            '{"summary": 1, "issues": [], "score": 8}',
            '{"summary": "ok", "issues": "x", "score": 8}',
            '{"summary": "ok", "issues": [], "score": true}',
        ):
            try:
                core.parse_model_json(text, SCHEMA)
            except core.SchemaError:
                continue
            raise AssertionError(f"类型错误应抛 SchemaError：{text}")

    def test_non_dict_json():
        for text in ("[1, 2]", '"text"', "123"):
            try:
                core.parse_model_json(text, SCHEMA)
            except core.SchemaError:
                continue
            raise AssertionError(f"非对象 JSON 应抛 SchemaError：{text}")

    def test_repair_success():
        calls = []

        def repair(raw: str) -> str:
            calls.append(raw)
            return '{"summary": "fixed", "issues": [], "score": 6}'

        data = core.parse_model_json("not json", SCHEMA, repair_fn=repair)
        expect(data["summary"] == "fixed", f"修复结果不对：{data}")
        expect(len(calls) == 1, f"repair 应只调用一次：{calls}")

    def test_repair_failure():
        calls = []

        def repair(raw: str) -> str:
            calls.append(raw)
            return "still bad"

        try:
            core.parse_model_json("bad", SCHEMA, repair_fn=repair)
        except core.SchemaError:
            expect(len(calls) == 1, "repair 应只调用一次")
            return
        raise AssertionError("修复失败应抛 SchemaError")

    def test_no_repair():
        try:
            core.parse_model_json("bad", SCHEMA)
        except core.SchemaError:
            return
        raise AssertionError("无 repair 时应直接抛 SchemaError")

    def test_validate_code_review_ok():
        data = core.validate_code_review({"summary": "  ok  ", "issues": ["a"], "score": 9})
        expect(data == {"summary": "ok", "issues": ["a"], "score": 9}, f"规范化不对：{data}")

    def test_validate_code_review_bad():
        bad = [
            {"summary": "", "issues": [], "score": 8},
            {"summary": "ok", "issues": "x", "score": 8},
            {"summary": "ok", "issues": [1], "score": 8},
            {"summary": "ok", "issues": [], "score": 0},
            {"summary": "ok", "issues": [], "score": 11},
            {"summary": "ok", "issues": [], "score": True},
        ]
        for data in bad:
            try:
                core.validate_code_review(data)
            except core.SchemaError:
                continue
            raise AssertionError(f"非法审查结果应抛 SchemaError：{data}")

    gate.check("01 解析纯 JSON", test_plain_json)
    gate.check("02 解析围栏与说明文字", test_fenced_and_prose)
    gate.check("03 拒绝缺字段", test_missing_field)
    gate.check("04 拒绝类型错误", test_wrong_type)
    gate.check("05 拒绝非对象 JSON", test_non_dict_json)
    gate.check("06 修复一次后成功", test_repair_success)
    gate.check("07 修复失败抛错", test_repair_failure)
    gate.check("08 无 repair 直接失败", test_no_repair)
    gate.check("09 代码审查结果通过", test_validate_code_review_ok)
    gate.check("10 拒绝非法代码审查", test_validate_code_review_bad)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
