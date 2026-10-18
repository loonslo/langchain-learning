"""L4.5 结构化路由 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALLOWED = {"research", "writing", "review", "finish"}
INTENTS = {"knowledge", "data_query", "chitchat"}


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l47", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l47"] = module
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
            "gate": "L4.5-structured-routing",
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

    def test_parse():
        expect(core.parse_route('{"next": "research", "reason": "x"}', ALLOWED) == "research", "解析不对")

    def test_parse_errors():
        bad = ["not json", '{"next": "delete"}', '{"reason": "x"}', '[]', "123"]
        for text in bad:
            try:
                core.parse_route(text, ALLOWED)
            except ValueError:
                continue
            raise AssertionError(f"应拒绝：{text}")

    def test_route_next():
        expect(core.route_next({"done": True, "_next": "research"}) == "end", "done 应 end")
        expect(core.route_next({"done": False, "_next": "writing"}) == "writing", "应返回 _next")
        try:
            core.route_next({"done": False, "_next": "delete"})
        except ValueError:
            return
        raise AssertionError("非法 _next 应抛 ValueError")

    def test_intent():
        for category in INTENTS:
            text = json.dumps({"category": category}, ensure_ascii=False)
            expect(core.parse_intent(text) == category, f"意图解析不对：{category}")
        try:
            core.parse_intent('{"category": "unknown"}')
        except ValueError:
            return
        raise AssertionError("未知意图应抛 ValueError")

    gate.check("01 枚举路由解析", test_parse)
    gate.check("02 拒绝非法路由", test_parse_errors)
    gate.check("03 路由函数", test_route_next)
    gate.check("04 意图解析", test_intent)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
