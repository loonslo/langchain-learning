"""L4.6 扩展 · 检查点与上下文 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l410", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l410"] = module
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
            "gate": "L4.6-checkpoint-context",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def messages() -> list[dict]:
    return [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "u3"},
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_checkpoint():
        store = core.CheckpointStore()
        store.save("t1", {"n": 1})
        expect(store.load("t1") == {"n": 1}, "保存/读取不对")
        expect(store.load("missing") is None, "缺失会话应返回 None")
        store.clear("t1")
        expect(store.load("t1") is None, "clear 后应为 None")

    def test_isolation():
        store = core.CheckpointStore()
        store.save("t1", {"n": 1})
        store.save("t2", {"n": 2})
        expect(store.load("t1") == {"n": 1} and store.load("t2") == {"n": 2}, "会话未隔离")
        try:
            store.save("", {})
        except ValueError:
            return
        raise AssertionError("空 thread_id 应抛 ValueError")

    def test_copy():
        store = core.CheckpointStore()
        state = {"items": [1]}
        store.save("t1", state)
        state["items"].append(2)
        expect(store.load("t1") == {"items": [1]}, "保存应复制，不能持有外部引用")

    def test_trim_system():
        rows = messages()
        trimmed = core.trim_history(rows, 3)
        expect(len(trimmed) == 3, f"应保留 3 条：{trimmed}")
        expect(trimmed[0]["role"] == "system", f"应保留 system：{trimmed}")
        expect([m["content"] for m in trimmed[1:]] == ["a2", "u3"], f"应保留最近两条：{trimmed}")

    def test_trim_no_system():
        rows = messages()[1:]
        trimmed = core.trim_history(rows, 2, keep_system=False)
        expect([m["content"] for m in trimmed] == ["a2", "u3"], f"应保留最近两条：{trimmed}")
        trimmed = core.trim_history(rows[:1], 5)
        expect(len(trimmed) == 1, "max 大于长度应返回全部")

    def test_trim_errors_and_mutation():
        rows = messages()
        original = copy.deepcopy(rows)
        core.trim_history(rows, 2)
        expect(rows == original, "不应修改输入")
        try:
            core.trim_history(rows, 0)
        except ValueError:
            return
        raise AssertionError("max_items=0 应抛 ValueError")

    gate.check("01 保存/读取/清除", test_checkpoint)
    gate.check("02 会话隔离", test_isolation)
    gate.check("03 保存副本", test_copy)
    gate.check("04 保留 system + 最近", test_trim_system)
    gate.check("05 无 system/长度不足", test_trim_no_system)
    gate.check("06 非法参数/不改输入", test_trim_errors_and_mutation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
