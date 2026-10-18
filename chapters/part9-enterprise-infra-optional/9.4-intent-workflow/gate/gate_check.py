"""L5.9 扩展 · 意图工作流 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


class FakeClassifier:
    def __init__(self, decision):
        self.decision = decision
        self.calls = 0

    def classify(self, question):
        self.calls += 1
        return self.decision


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l94", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l94"] = module
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
            "gate": "L5.9-intent-workflow",
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

    def workflow(intent="refund_status", confidence=0.99):
        return core.CustomerWorkflow(FakeClassifier({"intent": intent, "confidence": confidence}))

    def test_low_confidence():
        reply = workflow(confidence=0.5).handle("s1", "帮我退款")
        expect(reply["action"] == "handoff", f"低置信应转人工：{reply}")

    def test_unknown():
        reply = workflow(intent="unknown").handle("s1", "随便")
        expect(reply["action"] == "handoff", f"unknown 应转人工：{reply}")

    def test_human():
        reply = workflow(intent="human_handoff").handle("s1", "找人工")
        expect(reply["action"] == "handoff", f"human 应转人工：{reply}")

    def test_slot_flow():
        wf = workflow()
        first = wf.handle("s1", "我要退款")
        expect(first["action"] == "needs_slot" and "订单号" in first["reply"], f"应追问订单号：{first}")
        second = wf.handle("s1", "订单号 A100")
        expect(second["action"] == "ready" and second["values"]["order_id"] == "A100", f"补槽后应 ready：{second}")
        expect(wf.classifier.calls == 1, "补槽轮不应再次分类")

    def test_isolation():
        wf = workflow()
        wf.handle("s1", "我要退款")
        other = wf.handle("s2", "订单号 B200")
        expect(other["action"] == "ready" and other["values"]["order_id"] == "B200", f"会话应隔离：{other}")

    gate.check("01 低置信转人工", test_low_confidence)
    gate.check("02 unknown 转人工", test_unknown)
    gate.check("03 human 转人工", test_human)
    gate.check("04 槽位追问/补齐", test_slot_flow)
    gate.check("05 会话隔离", test_isolation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
