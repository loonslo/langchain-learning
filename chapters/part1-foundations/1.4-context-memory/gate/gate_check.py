"""L1.4 上下文与记忆 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l14", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l14"] = module
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
            "gate": "L1.4-context-memory",
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

    def sample_messages():
        return [
            {"role": "system", "content": "SYS"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
        ]

    def test_memory_add_get():
        memory = core.SessionMemory()
        memory.add("s1", "user", "你好")
        memory.add("s1", "assistant", "你好")
        rows = memory.get("s1")
        expect(rows == [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好"},
        ], f"历史不对：{rows}")

    def test_memory_isolated():
        memory = core.SessionMemory()
        memory.add("a", "user", "A")
        memory.add("b", "user", "B")
        expect(memory.get("a") == [{"role": "user", "content": "A"}], "会话 a 串台")
        expect(memory.get("b") == [{"role": "user", "content": "B"}], "会话 b 串台")

    def test_memory_get_copy():
        memory = core.SessionMemory()
        memory.add("s1", "user", "原值")
        rows = memory.get("s1")
        rows.append({"role": "user", "content": "外部修改"})
        expect(len(memory.get("s1")) == 1, "get 应返回副本")

    def test_memory_clear():
        memory = core.SessionMemory()
        memory.add("s1", "user", "x")
        memory.clear("s1")
        expect(memory.get("s1") == [], "clear 后应为空")
        memory.clear("missing")

    def test_memory_rejects_bad_input():
        memory = core.SessionMemory()
        for args in (("", "user", "x"), ("s", "tool", "x"), ("s", "user", 123)):
            try:
                memory.add(*args)
            except core.MemoryError:
                continue
            raise AssertionError(f"非法消息应拒绝：{args}")

    def test_trim_under_budget():
        messages = sample_messages()
        result = core.trim_history(messages, 100)
        expect(result == messages, f"预算足够应原样返回：{result}")

    def test_trim_over_budget():
        result = core.trim_history(sample_messages(), 4)
        expect(result == [
            {"role": "system", "content": "SYS"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
        ], f"裁剪结果不对：{result}")

    def test_trim_keeps_system_even_over_budget():
        messages = [{"role": "system", "content": "S" * 20}, {"role": "user", "content": "u"}]
        result = core.trim_history(messages, 0)
        expect(result == [{"role": "system", "content": "S" * 20}], f"system 应保留：{result}")

    def test_trim_order_and_no_mutation():
        messages = sample_messages()
        original = copy.deepcopy(messages)
        result = core.trim_history(messages, 5)
        expect(messages == original, "不应修改输入")
        roles = [row["role"] for row in result]
        expect(roles == ["system", "assistant", "user"], f"顺序不对：{roles}")

    def test_trim_empty():
        expect(core.trim_history([], 10) == [], "空列表应返回 []")

    def test_trim_rejects_negative():
        try:
            core.trim_history(sample_messages(), -1)
        except ValueError:
            return
        raise AssertionError("负预算应抛 ValueError")

    def test_trim_rejects_bad_message():
        for messages in ([{"role": "user"}], [{"role": "user", "content": 1}], [{"content": "x"}]):
            try:
                core.trim_history(messages, 10)
            except ValueError:
                continue
            raise AssertionError(f"非法消息应抛 ValueError：{messages}")

    gate.check("01 追加与读取", test_memory_add_get)
    gate.check("02 会话隔离", test_memory_isolated)
    gate.check("03 读取返回副本", test_memory_get_copy)
    gate.check("04 清空会话", test_memory_clear)
    gate.check("05 拒绝非法会话消息", test_memory_rejects_bad_input)
    gate.check("06 预算足够不裁剪", test_trim_under_budget)
    gate.check("07 超预算保留最近消息", test_trim_over_budget)
    gate.check("08 system 永远保留", test_trim_keeps_system_even_over_budget)
    gate.check("09 顺序保持且不修改输入", test_trim_order_and_no_mutation)
    gate.check("10 空历史", test_trim_empty)
    gate.check("11 拒绝负预算", test_trim_rejects_negative)
    gate.check("12 拒绝非法消息", test_trim_rejects_bad_message)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
