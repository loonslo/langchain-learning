"""L9 扩展 · A2A 任务状态机 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l102", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l102"] = module
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
            "gate": "L9-a2a-task",
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

    def test_submit():
        store = core.InMemoryTaskStore()
        task = store.submit(message_id="m1", message={"role": "user"})
        expect(task["state"] == "submitted" and task["id"], f"初始状态不对：{task}")
        again = store.submit(message_id="m1", message={"role": "user"})
        expect(again["id"] == task["id"], "同 message_id 应幂等")

    def test_empty():
        try:
            core.InMemoryTaskStore().submit(message_id="", message={})
        except ValueError:
            return
        raise AssertionError("空 message_id 应报错")

    def test_transitions():
        store = core.InMemoryTaskStore()
        task = store.submit(message_id="m1", message={})
        working = store.transition(task["id"], "working")
        expect(working["state"] == "working", "应进入 working")
        done = store.transition(task["id"], "completed", "ok")
        expect(done["state"] == "completed" and done.get("status_message") == "ok", f"应完成：{done}")

    def test_invalid():
        store = core.InMemoryTaskStore()
        task = store.submit(message_id="m1", message={})
        try:
            store.transition(task["id"], "completed")
        except core.TaskTransitionError:
            pass
        else:
            raise AssertionError("submitted->completed 应拒绝")
        store.transition(task["id"], "working")
        store.transition(task["id"], "completed")
        try:
            store.transition(task["id"], "working")
        except core.TaskTransitionError:
            return
        raise AssertionError("终态不应再迁移")

    def test_not_found():
        try:
            core.InMemoryTaskStore().get("missing")
        except core.TaskNotFound:
            return
        raise AssertionError("不存在应 TaskNotFound")

    gate.check("01 提交/幂等", test_submit)
    gate.check("02 空 message_id", test_empty)
    gate.check("03 合法迁移", test_transitions)
    gate.check("04 非法/终态迁移", test_invalid)
    gate.check("05 不存在任务", test_not_found)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
