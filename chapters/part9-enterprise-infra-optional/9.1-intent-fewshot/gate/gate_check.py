"""L9 意图 few-shot · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l91", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l91"] = module
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
            "gate": "L9-intent-fewshot",
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

    def test_prompt():
        prompt = core.build_intent_prompt("订单 A1 退款到哪了")
        for intent in ("refund_status", "order_status", "shipping", "human_handoff", "unknown"):
            expect(intent in prompt, f"提示词缺 {intent}")
        expect("订单 A1 退款到哪了" in prompt, "提示词缺用户问题")
        expect(prompt.count("用户：") >= 3, "示例不足 3 个")
        expect("JSON" in prompt, "缺 JSON 契约")
        try:
            core.build_intent_prompt("   ")
        except ValueError:
            return
        raise AssertionError("空问题应报错")

    def test_parse_dict():
        result = core.parse_intent_payload({"intent": "refund_status", "confidence": 0.98})
        expect(result["intent"] == "refund_status" and result["confidence"] == 0.98, f"解析不对：{result}")

    def test_parse_str():
        result = core.parse_intent_payload('{"intent":"human_handoff","confidence":1}')
        expect(result["intent"] == "human_handoff" and result["confidence"] == 1.0, f"字符串解析不对：{result}")

    def test_bad_intent():
        for payload in ({"intent": "refund", "confidence": 0.9}, {"intent": "unknown"}, {"confidence": 0.9}, "[]", "bad"):
            try:
                core.parse_intent_payload(payload)
            except ValueError:
                continue
            raise AssertionError(f"非法输出应报错：{payload}")

    def test_confidence():
        for value in (-0.1, 1.1, "high"):
            try:
                core.parse_intent_payload({"intent": "unknown", "confidence": value})
            except ValueError:
                continue
            raise AssertionError(f"非法置信度应报错：{value}")

    gate.check("01 提示词", test_prompt)
    gate.check("02 dict 解析", test_parse_dict)
    gate.check("03 字符串解析", test_parse_str)
    gate.check("04 非法意图/缺字段", test_bad_intent)
    gate.check("05 置信度范围", test_confidence)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
