"""L5.9 槽位填充 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l92", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l92"] = module
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
            "gate": "L5.9-slot-filling",
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

    def test_extract():
        expect(core.extract_slots("订单号：ab-123") == {"order_id": "AB-123"}, "中文订单号解析不对")
        expect(core.extract_slots("order id: x9") == {"order_id": "X9"}, "英文订单号解析不对")
        expect(core.extract_slots("你好") == {}, "无订单号应为空")

    def test_merge():
        state = core.resolve_slots("refund_status", "订单号 A1")
        expect(state["intent"] == "refund_status" and state["missing"] == (), f"应齐全：{state}")
        expect(state["values"]["order_id"] == "A1", f"值不对：{state}")

    def test_previous():
        prev = {"order_id": "OLD"}
        state = core.resolve_slots("order_status", "订单号 NEW1", prev)
        expect(state["values"]["order_id"] == "NEW1", f"新值应覆盖：{state}")
        expect(prev == {"order_id": "OLD"}, "不应修改 previous")

    def test_missing():
        state = core.resolve_slots("refund_status", "我要退款")
        expect(state["missing"] == ("order_id",), f"应缺订单号：{state}")
        expect(core.next_question(state) is not None, "应追问")
        expect(core.next_question(core.resolve_slots("shipping", "到哪了")) is None, "无必填不应追问")

    def test_unknown_intent():
        try:
            core.resolve_slots("refund", "x")
        except ValueError:
            return
        raise AssertionError("未知 intent 应抛 ValueError")

    gate.check("01 提取订单号", test_extract)
    gate.check("02 合并槽位", test_merge)
    gate.check("03 上一轮覆盖", test_previous)
    gate.check("04 缺失与追问", test_missing)
    gate.check("05 未知意图", test_unknown_intent)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
