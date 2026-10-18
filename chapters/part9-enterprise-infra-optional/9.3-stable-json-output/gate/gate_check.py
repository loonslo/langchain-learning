"""L1.3 扩展 · 稳定 JSON 契约 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDS = {"title": str, "score": int, "ok": bool}


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l93", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l93"] = module
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
            "gate": "L1.3-json-contract",
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

    def test_fenced():
        text = '```json\n{"title":"x","score":1,"ok":true}\n```'
        result = core.parse_model_json(text, FIELDS)
        expect(result == {"title": "x", "score": 1, "ok": True}, f"围栏解析不对：{result}")

    def test_strict_types():
        for text in ('{"title":"x","score":true,"ok":true}', '{"title":1,"score":1,"ok":true}'):
            try:
                core.parse_model_json(text, FIELDS)
            except core.StructuredOutputError:
                continue
            raise AssertionError("类型不严格应报错")

    def test_missing_extra():
        for text in ('{"title":"x","score":1}', '{"title":"x","score":1,"ok":true,"z":1}'):
            try:
                core.parse_model_json(text, FIELDS)
            except core.StructuredOutputError:
                continue
            raise AssertionError("缺字段/多余字段应报错")
        result = core.parse_model_json('{"title":"x","score":1,"ok":true,"z":1}', FIELDS, allow_extra=True)
        expect(result == {"title": "x", "score": 1, "ok": True}, "allow_extra 应只返回声明字段")

    def test_not_object():
        for text in ('["x"]', 'not json'):
            try:
                core.parse_model_json(text, FIELDS)
            except core.StructuredOutputError:
                continue
            raise AssertionError("非对象/坏 JSON 应报错")

    def test_repair_once():
        calls = {"n": 0}

        def repair(_text):
            calls["n"] += 1
            return '{"title":"fixed","score":2,"ok":true}'

        result = core.parse_model_json("bad", FIELDS, repair=repair)
        expect(result["title"] == "fixed" and calls["n"] == 1, f"应 repair 一次：{result}, {calls}")

    def test_repair_fails():
        def repair(_text):
            return "still bad"

        try:
            core.parse_model_json("bad", FIELDS, repair=repair)
        except core.StructuredOutputError:
            return
        raise AssertionError("repair 失败应抛错")

    gate.check("01 围栏 JSON", test_fenced)
    gate.check("02 严格类型", test_strict_types)
    gate.check("03 缺/多字段", test_missing_extra)
    gate.check("04 非对象", test_not_object)
    gate.check("05 repair 一次", test_repair_once)
    gate.check("06 repair 失败", test_repair_fails)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
