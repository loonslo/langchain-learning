"""L1.1 一次调用 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l11", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l11"] = module
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
            "gate": "L1.1-first-call",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


class ScriptedChat:
    def __init__(self, response):
        self.response = response
        self.calls: list[list[dict]] = []

    def __call__(self, messages: list[dict]):
        self.calls.append(messages)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_build_messages():
        messages = core.build_messages("你是老师", "什么是 RAG")
        expect(messages == [
            {"role": "system", "content": "你是老师"},
            {"role": "user", "content": "什么是 RAG"},
        ], f"消息结构不对：{messages}")

    def test_build_rejects_empty():
        for system, question in (("", "q"), ("s", ""), ("   ", "q")):
            try:
                core.build_messages(system, question)
            except ValueError:
                continue
            raise AssertionError(f"空参数应抛 ValueError：{system!r}, {question!r}")

    def test_parse_valid():
        parsed = core.parse_response({
            "content": "你好",
            "usage": {"input_tokens": 3, "output_tokens": 2},
            "finish_reason": "stop",
        })
        expect(parsed["content"] == "你好", "content 不对")
        expect(parsed["input_tokens"] == 3 and parsed["output_tokens"] == 2, "token 不对")
        expect(parsed["finish_reason"] == "stop", "finish_reason 不对")

    def test_parse_missing_usage_defaults_zero():
        parsed = core.parse_response({"content": "你好"})
        expect(parsed["input_tokens"] == 0 and parsed["output_tokens"] == 0, "缺失 usage 应记 0")
        expect(parsed["finish_reason"] == "stop", "缺省 finish_reason 应为 stop")

    def test_parse_errors():
        bad = [
            ["not a dict"],
            {},
            {"content": None},
            {"content": "   "},
            {"content": 123},
        ]
        for response in bad:
            try:
                core.parse_response(response)
            except core.CallError:
                continue
            raise AssertionError(f"非法响应应抛 CallError：{response!r}")

    def test_call_success():
        chat = ScriptedChat({"content": "答案", "usage": {"input_tokens": 5, "output_tokens": 1}})
        result = core.call_once("system", "问题", chat)
        expect(result["content"] == "答案" and result["error"] is None, f"结果不对：{result}")
        expect(chat.calls and chat.calls[0][1]["content"] == "问题", "chat_fn 没收到问题")

    def test_call_empty_question():
        try:
            core.call_once("system", "  ", ScriptedChat({"content": "x"}))
        except ValueError:
            return
        raise AssertionError("空问题应抛 ValueError")

    def test_call_timeout():
        result = core.call_once("system", "问题", ScriptedChat(TimeoutError("timeout")))
        expect(result["error"] == "timeout", f"error 应为 timeout：{result}")
        expect(result["content"] == "", "超时时 content 应为空")

    def test_call_model_error():
        result = core.call_once("system", "问题", ScriptedChat(RuntimeError("boom")))
        expect(result["error"] == "model_error", f"error 应为 model_error：{result}")

    def test_call_empty_response():
        result = core.call_once("system", "问题", ScriptedChat({"content": ""}))
        expect(result["error"] == "empty_response", f"error 应为 empty_response：{result}")

    def test_call_bad_response():
        result = core.call_once("system", "问题", ScriptedChat(["bad"]))
        expect(result["error"] == "bad_response", f"error 应为 bad_response：{result}")

    gate.check("01 消息结构与顺序", test_build_messages)
    gate.check("02 拒绝空 system/question", test_build_rejects_empty)
    gate.check("03 解析正常响应", test_parse_valid)
    gate.check("04 缺 usage 记 0", test_parse_missing_usage_defaults_zero)
    gate.check("05 拒绝非法响应", test_parse_errors)
    gate.check("06 一次调用成功", test_call_success)
    gate.check("07 空问题拒绝", test_call_empty_question)
    gate.check("08 超时降级", test_call_timeout)
    gate.check("09 模型异常降级", test_call_model_error)
    gate.check("10 空响应降级", test_call_empty_response)
    gate.check("11 非法响应降级", test_call_bad_response)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
