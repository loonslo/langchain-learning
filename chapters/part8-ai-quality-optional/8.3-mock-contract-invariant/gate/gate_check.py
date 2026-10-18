"""L8 契约与不变量 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l83", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l83"] = module
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
            "gate": "L8-contracts",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def payload(**overrides) -> dict:
    base = {"answer": "已发货", "sources": ["docs/a.md"], "ticket_id": None}
    base.update(overrides)
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_valid():
        expect(core.validate_chat_response(payload()) == [], f"合法响应不应报错：{core.validate_chat_response(payload())}")

    def test_contract_errors():
        cases = [
            payload(answer=" "),
            payload(sources="a"),
            payload(sources=[""]),
            payload(ticket_id=1),
        ]
        for item in cases:
            expect(core.validate_chat_response(item), f"应报契约错误：{item}")

    def test_collect_all():
        errors = core.validate_chat_response({"answer": "", "sources": "bad", "ticket_id": 1})
        expect(len(errors) == 3, f"应一次报 3 条：{errors}")

    def test_refusal_source():
        bad = payload(answer="没有足够信息", sources=["x"])
        try:
            core.assert_invariants(bad)
        except AssertionError:
            pass
        else:
            raise AssertionError("拒答带来源应失败")
        core.assert_invariants(payload(answer="没有足够信息", sources=[]))

    def test_ticket_handoff():
        bad = payload(answer="已处理", sources=[], ticket_id="T1")
        try:
            core.assert_invariants(bad)
        except AssertionError:
            pass
        else:
            raise AssertionError("无来源工单未说明人工应失败")
        core.assert_invariants(payload(answer="已转人工", sources=[], ticket_id="T1"))

    gate.check("01 合法响应", test_valid)
    gate.check("02 契约错误", test_contract_errors)
    gate.check("03 一次收集", test_collect_all)
    gate.check("04 拒答不带来源", test_refusal_source)
    gate.check("05 工单转人工", test_ticket_handoff)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
