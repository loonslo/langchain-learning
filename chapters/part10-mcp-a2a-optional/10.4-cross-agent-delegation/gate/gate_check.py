"""L10 扩展 · 跨 Agent 委派 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Reader:
    def status(self, *, tenant_id, subject, order_id):
        return f"{tenant_id}/{subject}/{order_id}:已发货"


class Client:
    def __init__(self, response):
        self.response = response

    def send_order_question(self, text, context):
        return self.response


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l104", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l104"] = module
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
            "gate": "L10-delegation",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


CONTEXT = {"tenant_id": "shop-a", "subject": "u1", "scopes": ("orders.read",), "request_id": "r1"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_missing_order():
        result = core.OrderAgent(Reader(), CONTEXT).handle("订单到哪了")
        expect(result["state"] == "input-required", f"缺订单号应追问：{result}")

    def test_auth():
        context = dict(CONTEXT, scopes=())
        result = core.OrderAgent(Reader(), context).handle("订单 A100 到哪了")
        expect(result["state"] == "auth-required", f"缺 scope 应 auth：{result}")

    def test_success():
        result = core.OrderAgent(Reader(), CONTEXT).handle("订单 A100 到哪了")
        expect(result["state"] == "completed" and "已发货" in result["message"], f"应完成：{result}")
        expect("shop-a/u1/A100" in result["message"], f"应传租户/主体/订单：{result}")

    def test_delegate_ok():
        response = {"result": {"status": {"state": "completed", "message": {"parts": [{"text": "已发货"}]}}}}
        text = core.SupportOrderDelegator(Client(response)).handle("q", CONTEXT)
        expect(text == "已发货", f"应返回 message：{text}")

    def test_delegate_errors():
        error = {"error": {"code": -32001}}
        expect("人工" in core.SupportOrderDelegator(Client(error)).handle("q", CONTEXT), "error 应转人工")
        input_required = {"result": {"status": {"state": "input-required", "message": {"parts": [{"text": "请提供订单号"}]}}}}
        expect(core.SupportOrderDelegator(Client(input_required)).handle("q", CONTEXT) == "请提供订单号", "input 应原样追问")
        auth = {"result": {"status": {"state": "auth-required", "message": {"parts": [{"text": "x"}]}}}}
        expect("无权" in core.SupportOrderDelegator(Client(auth)).handle("q", CONTEXT), "auth 应无权限提示")

    gate.check("01 缺订单号", test_missing_order)
    gate.check("02 缺 scope", test_auth)
    gate.check("03 正常查询", test_success)
    gate.check("04 委托成功", test_delegate_ok)
    gate.check("05 委托错误/追问/无权限", test_delegate_errors)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
