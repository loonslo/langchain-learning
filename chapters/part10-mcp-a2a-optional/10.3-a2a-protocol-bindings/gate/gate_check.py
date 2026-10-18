"""L10 扩展 · A2A JSON-RPC 绑定 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l103", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l103"] = module
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
            "gate": "L10-jsonrpc",
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

    class App(core.A2AApplication):
        def send(self, params):
            if params.get("message") == "bad":
                raise ValueError("bad message")
            return {"kind": "task", "id": "t1"}

        def get(self, task_id):
            if task_id == "missing":
                raise core.TaskNotFound(task_id)
            if task_id == "bad":
                raise KeyError("id")
            return {"kind": "task", "id": task_id}

        def cancel(self, task_id):
            return {"kind": "task", "id": task_id, "state": "canceled"}

    app = App()

    def req(method, params=None, request_id=1):
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        return payload

    def test_send():
        response = app.dispatch(req("message/send", {"message": {"x": 1}}))
        expect(response["id"] == 1 and response["result"]["id"] == "t1", f"send 响应不对：{response}")

    def test_get_cancel():
        expect(app.dispatch(req("tasks/get", {"id": "t9"}))["result"]["id"] == "t9", "get 不对")
        expect(app.dispatch(req("tasks/cancel", {"id": "t9"}))["result"]["state"] == "canceled", "cancel 不对")

    def test_invalid_request():
        for payload in ({"jsonrpc": "1.0", "id": 1, "method": "x"}, {"jsonrpc": "2.0", "id": 1}):
            expect(app.dispatch(payload)["error"]["code"] == -32600, f"应 -32600：{payload}")

    def test_invalid_params():
        expect(app.dispatch(req("message/send", "bad"))["error"]["code"] == -32602, "params 非对象应 -32602")
        expect(app.dispatch(req("tasks/get", {"id": "bad"}))["error"]["code"] == -32602, "KeyError 应 -32602")
        expect(app.dispatch(req("message/send", {"message": "bad"}))["error"]["code"] == -32602, "ValueError 应 -32602")

    def test_not_found():
        response = app.dispatch(req("tasks/get", {"id": "missing"}))
        expect(response["error"]["code"] == -32001, f"TaskNotFound 应 -32001：{response}")

    def test_unknown_method():
        expect(app.dispatch(req("tasks/unknown"))["error"]["code"] == -32601, "未知方法应 -32601")

    gate.check("01 message/send", test_send)
    gate.check("02 tasks/get+cancel", test_get_cancel)
    gate.check("03 无效请求", test_invalid_request)
    gate.check("04 无效参数", test_invalid_params)
    gate.check("05 任务不存在", test_not_found)
    gate.check("06 未知方法", test_unknown_method)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
