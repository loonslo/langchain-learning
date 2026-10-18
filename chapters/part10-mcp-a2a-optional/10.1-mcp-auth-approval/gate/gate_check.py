"""L9 扩展 · MCP 授权 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l101", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l101"] = module
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
            "gate": "L9-mcp-auth",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def claims(**overrides) -> dict:
    base = {"subject": "u1", "audience": ["mcp://kb"], "scopes": ["kb.read"], "tenant_id": "t1"}
    base.update(overrides)
    return base


def policy(**overrides) -> dict:
    base = {"name": "search", "required_scope": "kb.read", "requires_human_approval": False}
    base.update(overrides)
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_pass():
        core.authorize_tool(claims(), policy(), resource_audience="mcp://kb")

    def test_audience():
        try:
            core.authorize_tool(claims(audience=["mcp://other"]), policy(), resource_audience="mcp://kb")
        except core.McpAuthorizationError:
            return
        raise AssertionError("audience 不匹配应拒绝")

    def test_scope():
        try:
            core.authorize_tool(claims(scopes=[]), policy(), resource_audience="mcp://kb")
        except core.McpAuthorizationError:
            return
        raise AssertionError("缺 scope 应拒绝")

    def test_approval():
        high = policy(requires_human_approval=True)
        try:
            core.authorize_tool(claims(), high, resource_audience="mcp://kb")
        except core.McpAuthorizationError:
            pass
        else:
            raise AssertionError("高风险未审批应拒绝")
        core.authorize_tool(claims(), high, resource_audience="mcp://kb", approved=True)

    def test_order():
        try:
            core.authorize_tool(claims(audience=[], scopes=[]), policy(requires_human_approval=True), resource_audience="mcp://kb")
        except core.McpAuthorizationError:
            return
        raise AssertionError("应先报 audience")

    gate.check("01 合法授权", test_pass)
    gate.check("02 audience", test_audience)
    gate.check("03 scope", test_scope)
    gate.check("04 高风险审批", test_approval)
    gate.check("05 检查顺序", test_order)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
