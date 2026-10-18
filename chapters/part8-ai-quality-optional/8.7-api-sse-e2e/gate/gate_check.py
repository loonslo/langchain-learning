"""L8 API/SSE E2E · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l87", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l87"] = module
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
            "gate": "L8-sse-e2e",
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
        payload = "event: token\nid: 1\ndata: {\"text\": \"你\"}\n\ndata: world\n\n: comment\n"
        events = core.parse_sse(payload)
        expect(len(events) == 2, f"应解析 2 个事件：{events}")
        expect(events[0]["event"] == "token" and events[0]["event_id"] == "1", f"事件字段不对：{events[0]}")
        expect(events[1]["event"] == "message" and events[1]["data"] == "world", f"默认事件/数据不对：{events[1]}")

    def test_multiline():
        events = core.parse_sse("data: a\ndata: b\n\n")
        expect(events[0]["data"] == "a\nb", f"多行 data 应换行连接：{events}")

    def test_empty_no_data():
        expect(core.parse_sse("event: x\n\n") == [], "无 data 块应丢弃")

    def test_combine():
        events = [
            {"event": "token", "data": '{"text": "你"}'},
            {"event": "token", "data": '{"text": "好"}'},
            {"event": "done", "data": "x"},
            {"event": "message", "data": "plain"},
            {"event": "token", "data": "[1,2]"},
        ]
        expect(core.combine_text(events) == "你好plain[1, 2]" or core.combine_text(events) == "你好plain[1,2]", f"拼接不对：{core.combine_text(events)}")

    def test_e2e():
        good = {"answer": "a", "sources": [], "request_id": "r1"}
        expect(core.validate_e2e_response(good) == [], f"合法响应不应报错：{core.validate_e2e_response(good)}")
        expect(core.validate_e2e_response({"answer": "a", "sources": [], "request_id": 1}), "request_id 非字符串应报错")

    gate.check("01 SSE 事件", test_parse)
    gate.check("02 多行 data", test_multiline)
    gate.check("03 无 data 丢弃", test_empty_no_data)
    gate.check("04 文本拼接", test_combine)
    gate.check("05 E2E 契约", test_e2e)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
