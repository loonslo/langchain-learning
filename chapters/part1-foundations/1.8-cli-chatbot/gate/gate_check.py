"""L1.7 CLI 助手 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l18", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l18"] = module
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
            "gate": "L1.7-cli-chatbot",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


class ScriptedChat:
    def __init__(self, replies: list[dict | Exception]):
        self.replies = list(replies)
        self.calls: list[list[dict]] = []

    def __call__(self, messages: list[dict]) -> dict:
        self.calls.append([dict(row) for row in messages])
        if not self.replies:
            raise AssertionError("chat_fn 调用次数超过预设")
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def reply(content: str) -> dict:
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

    def test_one_turn():
        chat = ScriptedChat([reply("你好")])
        result = core.run_cli(["在吗"], chat)
        expect(result["outputs"][-1] == "你好", f"输出不对：{result['outputs']}")
        expect(result["exit_code"] == 0, f"exit_code 应为 0：{result['exit_code']}")
        expect(result["history"][0] == {"role": "system", "content": core.SYSTEM_PROMPT}, "历史应以 system 开始")
        expect(any(row.get("role") == "user" and row.get("content") == "在吗" for row in result["history"]), "历史缺 user")

    def test_multi_turn_history():
        chat = ScriptedChat([reply("第一次"), reply("第二次")])
        result = core.run_cli(["一", "二"], chat)
        expect(len(chat.calls) == 2, f"应调用两次：{len(chat.calls)}")
        second = chat.calls[1]
        expect(any(row.get("role") == "assistant" and row.get("content") == "第一次" for row in second), "第二轮没带上一轮回答")
        expect(result["outputs"] == ["第一次", "第二次"], f"输出不对：{result['outputs']}")

    def test_clear():
        chat = ScriptedChat([reply("第一"), reply("第二")])
        result = core.run_cli(["一", "clear", "二"], chat)
        expect("记忆已清除" in result["outputs"], f"clear 输出不对：{result['outputs']}")
        second = chat.calls[1]
        expect(not any(row.get("content") == "第一" for row in second), "clear 后不应带旧历史")
        expect(any(row.get("content") == "二" for row in second), "clear 后应带新问题")

    def test_quit():
        chat = ScriptedChat([reply("一次")])
        result = core.run_cli(["一", "quit", "二"], chat)
        expect(len(chat.calls) == 1, f"quit 后不应继续调用：{len(chat.calls)}")
        expect(result["exit_code"] == 0, "quit 应正常退出")

    def test_empty_inputs():
        chat = ScriptedChat([])
        result = core.run_cli(["", "   "], chat)
        expect(result["outputs"] == [] and result["exit_code"] == 0, f"空输入结果不对：{result}")
        expect(chat.calls == [], "空输入不应调用模型")

    def test_tool_then_final():
        chat = ScriptedChat([call("weather", {"city": "北京"}), reply("北京晴天")])
        result = core.run_cli(["天气"], chat, tools={"weather": lambda args: "晴天"})
        expect(result["outputs"][-1] == "北京晴天", f"最终输出不对：{result['outputs']}")
        expect(len(chat.calls) == 2, "工具调用后应再问一次模型")
        second = chat.calls[1]
        expect(any(
            row.get("role") == "tool" and row.get("tool_call_id") == "c1" and row.get("content") == "晴天"
            for row in second
        ), f"工具结果没有回灌：{second}")

    def test_unknown_tool():
        chat = ScriptedChat([call("nope", {})])
        result = core.run_cli(["x"], chat, tools={})
        expect(result["exit_code"] == 1, f"未知工具 exit_code 应为 1：{result}")
        expect(any("工具" in output for output in result["outputs"]), f"应有工具错误：{result['outputs']}")

    def test_model_error():
        chat = ScriptedChat([TimeoutError("timeout")])
        result = core.run_cli(["x"], chat)
        expect(result["exit_code"] == 1, "模型异常 exit_code 应为 1")
        expect(any("模型" in output for output in result["outputs"]), f"应有模型错误：{result['outputs']}")

    def test_max_turns():
        chat = ScriptedChat([reply("一"), reply("二")])
        result = core.run_cli(["1", "2", "3"], chat, max_turns=2)
        expect(result["exit_code"] == 2, f"超轮数 exit_code 应为 2：{result}")
        expect(result["outputs"][:2] == ["一", "二"], f"前两轮输出不对：{result['outputs']}")
        expect(any("最大轮数" in output for output in result["outputs"]), "应提示达到最大轮数")

    def test_max_turns_validation():
        try:
            core.run_cli([], ScriptedChat([]), max_turns=0)
        except core.CLIError:
            return
        raise AssertionError("max_turns<1 应抛 CLIError")

    def test_no_inputs():
        result = core.run_cli([], ScriptedChat([]))
        expect(result["exit_code"] == 0, "无输入应正常退出")
        expect(result["history"] == [{"role": "system", "content": core.SYSTEM_PROMPT}], "历史应只有 system")

    gate.check("01 单轮对话", test_one_turn)
    gate.check("02 多轮历史", test_multi_turn_history)
    gate.check("03 clear 清空记忆", test_clear)
    gate.check("04 quit 停止", test_quit)
    gate.check("05 空输入忽略", test_empty_inputs)
    gate.check("06 工具调用后收尾", test_tool_then_final)
    gate.check("07 未知工具错误", test_unknown_tool)
    gate.check("08 模型异常错误", test_model_error)
    gate.check("09 超过最大轮数", test_max_turns)
    gate.check("10 max_turns 参数校验", test_max_turns_validation)
    gate.check("11 无输入", test_no_inputs)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
