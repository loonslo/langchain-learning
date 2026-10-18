"""L4.3 状态与 Reducer · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from langgraph.errors import InvalidUpdateError

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l44", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l44"] = module
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
            "gate": "L4.3-state-reducer",
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

    def test_merge():
        old, new = ["a"], ["b"]
        expect(core.merge_lists(old, new) == ["a", "b"], "merge_lists 不对")
        expect(old == ["a"] and new == ["b"], "不应修改输入")

    def test_window():
        expect(core.keep_last_n(["1", "2", "3"], ["4"], 3) == ["2", "3", "4"], "滑动窗口不对")
        expect(core.keep_last_n([], ["1"], 1) == ["1"], "空旧值不对")
        try:
            core.keep_last_n([], [], 0)
        except ValueError:
            return
        raise AssertionError("n<1 应抛 ValueError")

    def test_accumulate():
        result = core.build_accumulate_graph().invoke({"log": []})
        expect(result["log"] == ["A", "B"], f"累加结果不对：{result}")

    def test_fanout():
        result = core.build_fanout_graph().invoke({"results": []})
        expect(len(result["results"]) == 3, f"fan-out 应保留 3 条：{result}")

    def test_no_reducer():
        try:
            core.build_fanout_no_reducer().invoke({"results": []})
        except InvalidUpdateError:
            return
        raise AssertionError("无 reducer 的 fan-out 应抛 InvalidUpdateError")

    gate.check("01 merge_lists", test_merge)
    gate.check("02 滑动窗口", test_window)
    gate.check("03 累加图", test_accumulate)
    gate.check("04 fan-out 保留全部", test_fanout)
    gate.check("05 无 reducer 报错", test_no_reducer)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
