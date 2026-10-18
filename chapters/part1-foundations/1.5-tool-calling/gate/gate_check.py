"""L1.5 工具调用 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l15", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l15"] = module
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
            "gate": "L1.5-tool-calling",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


class ScriptedLLM:
    def __init__(self, replies: list[dict | Exception]):
        self.replies = list(replies)
        self.calls: list[list[dict]] = []

    def __call__(self, messages: list[dict]) -> dict:
        self.calls.append([dict(row) for row in messages])
        if not self.replies:
            raise AssertionError("llm_fn 调用次数超过预设")
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def final(content: str) -> dict:
    return {"content": content, "tool_calls": []}


def call(tool: str, args: dict, call_id: str = "c1") -> dict:
    return {"content": "", "tool_calls": [{"id": call_id, "name": tool, "args": args}]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_tools_contract():
        tools = core.build_tools()
        expect(set(tools) == {"get_weather", "calculate"}, f"工具表不对：{set(tools)}")
        expect(tools["get_weather"].parameters == {"city": str}, "weather 参数不对")
        expect(tools["calculate"].parameters == {"expression": str}, "calculate 参数不对")
        expect(tools["get_weather"].description.strip(), "description 不能为空")
        expect(tools["get_weather"].handler({"city": "北京"}).strip(), "weather handler 结果不能为空")
        expect(tools["calculate"].handler({"expression": "2+2"}) == "4", "calculate handler 结果不对")

    def test_dispatch_valid():
        tools = core.build_tools()
        result = core.dispatch_tool(tools, "calculate", {"expression": "3*3"})
        expect(result["ok"] is True and result["result"] == "9" and result["error"] is None, f"分发结果不对：{result}")

    def test_dispatch_errors():
        tools = core.build_tools()
        cases = [
            (("nope", {}), "unknown_tool"),
            (("get_weather", ["北京"]), "invalid_args"),
            (("get_weather", {}), "invalid_args"),
            (("get_weather", {"city": 1}), "invalid_args"),
        ]
        for (name, args), expected in cases:
            result = core.dispatch_tool(tools, name, args)
            expect(result["ok"] is False and result["error"] == expected, f"错误不对：{result}")

    def test_dispatch_tool_exception():
        tools = core.build_tools()
        tools["get_weather"] = core.ToolSpec(
            "get_weather", "天气", {"city": str}, lambda args: (_ for _ in ()).throw(RuntimeError("down"))
        )
        result = core.dispatch_tool(tools, "get_weather", {"city": "北京"})
        expect(result["ok"] is False and result["error"] == "tool_error", f"工具异常不对：{result}")

    def test_loop_final_without_tools():
        llm = ScriptedLLM([final("直接回答")])
        result = core.run_tool_loop([{"role": "user", "content": "你好"}], llm)
        expect(result["answer"] == "直接回答" and result["stopped_reason"] == "final", f"结果不对：{result}")
        expect(result["trace"] == [], "没有工具调用时 trace 应为空")

    def test_loop_tool_then_final():
        llm = ScriptedLLM([call("get_weather", {"city": "北京"}), final("北京晴天")])
        result = core.run_tool_loop([{"role": "user", "content": "天气"}], llm)
        expect(result["answer"] == "北京晴天" and result["stopped_reason"] == "final", f"结果不对：{result}")
        expect(len(result["trace"]) == 1, f"trace 应有 1 步：{result['trace']}")
        step = result["trace"][0]
        expect(step["tool"] == "get_weather" and step["ok"] is True, f"trace 不对：{step}")
        second_messages = llm.calls[1]
        expect(any(
            row.get("role") == "tool" and row.get("tool_call_id") == "c1" and row.get("content", "").strip()
            for row in second_messages
        ), f"工具结果没有回灌：{second_messages}")

    def test_loop_unknown_tool():
        llm = ScriptedLLM([call("nope", {}), final("未知工具")])
        result = core.run_tool_loop([{"role": "user", "content": "x"}], llm)
        expect(result["trace"][0]["ok"] is False and result["trace"][0]["error"] == "unknown_tool", f"trace 不对：{result['trace']}")
        expect(result["stopped_reason"] == "final", "未知工具后仍应允许收尾")

    def test_loop_tool_exception():
        tools = core.build_tools()
        tools["get_weather"] = core.ToolSpec(
            "get_weather", "天气", {"city": str}, lambda args: (_ for _ in ()).throw(RuntimeError("down"))
        )
        llm = ScriptedLLM([call("get_weather", {"city": "北京"}), final("工具失败")])
        result = core.run_tool_loop([{"role": "user", "content": "x"}], llm, tools=tools)
        expect(result["trace"][0]["error"] == "tool_error", f"trace 不对：{result['trace']}")

    def test_loop_max_steps():
        llm = ScriptedLLM([call("calculate", {"expression": "1+1"})] * 2)
        result = core.run_tool_loop([{"role": "user", "content": "x"}], llm, max_steps=2)
        expect(result["stopped_reason"] == "max_steps", "应在 max_steps 停止")
        expect(len(result["trace"]) == 2, f"trace 应为 2 步：{len(result['trace'])}")

    def test_loop_model_error():
        result = core.run_tool_loop([{"role": "user", "content": "x"}], ScriptedLLM([TimeoutError("timeout")]))
        expect(result["stopped_reason"] == "model_error", "模型异常应标记 model_error")
        expect(result["answer"], "应给出可读提示")

    def test_loop_rejects_zero_steps():
        try:
            core.run_tool_loop([{"role": "user", "content": "x"}], ScriptedLLM([]), max_steps=0)
        except ValueError:
            return
        raise AssertionError("max_steps<1 应抛 ValueError")

    gate.check("01 工具表与元数据", test_tools_contract)
    gate.check("02 分发合法调用", test_dispatch_valid)
    gate.check("03 未知工具/参数错误", test_dispatch_errors)
    gate.check("04 工具异常", test_dispatch_tool_exception)
    gate.check("05 无工具直接回答", test_loop_final_without_tools)
    gate.check("06 工具结果回灌后收尾", test_loop_tool_then_final)
    gate.check("07 未知工具可读失败", test_loop_unknown_tool)
    gate.check("08 工具异常可读失败", test_loop_tool_exception)
    gate.check("09 最大步数终止", test_loop_max_steps)
    gate.check("10 模型异常终止", test_loop_model_error)
    gate.check("11 max_steps 参数校验", test_loop_rejects_zero_steps)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
