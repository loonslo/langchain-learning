"""L4.1 Agent 模式 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l41", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l41"] = module
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
            "gate": "L4.1-agent-patterns",
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

    def test_fixed_workflow():
        expect(core.fixed_workflow(2, 3) == 5, "2+3 应为 5")
        for args in ((True, 3), ("2", 3), (2, 3.5)):
            try:
                core.fixed_workflow(*args)
            except ValueError:
                continue
            raise AssertionError(f"非整数应抛 ValueError：{args}")

    def test_initial_state():
        state = core.initial_state()
        for key in ("question", "steps", "observations", "decision", "status", "error"):
            expect(key in state, f"初始 state 缺 {key}")
        expect(state["steps"] == 0 and state["observations"] == [], "初始 steps/observations 不对")

    def test_normal_loop():
        result = core.build_graph().invoke(core.initial_state())
        expect(result["status"] == "done", f"正常应 done：{result}")
        expect(result["observations"] == [5] and result["steps"] == 1, f"结果不对：{result}")

    def test_budget():
        graph = core.build_graph(lambda _: {"action": "add", "a": 2, "b": 3}, max_steps=2)
        result = graph.invoke(core.initial_state())
        expect(result["status"] == "failed" and "预算" in result["error"], f"应预算耗尽：{result}")
        expect(result["steps"] == 2, f"应执行 2 步：{result}")

    def test_unknown_tool():
        graph = core.build_graph(lambda _: {"action": "delete", "a": 1, "b": 1})
        result = graph.invoke(core.initial_state())
        expect(result["status"] == "failed" and "白名单" in result["error"], f"未知工具应拦截：{result}")

    def test_planner_error():
        def boom(_state):
            raise ValueError("planner down")

        result = core.build_graph(boom).invoke(core.initial_state())
        expect(result["status"] == "failed" and "planner down" in result["error"], f"应记录 planner 错误：{result}")

    def test_bad_params():
        graph = core.build_graph(lambda _: {"action": "add", "a": "x", "b": 3})
        result = graph.invoke(core.initial_state())
        expect(result["status"] == "failed", f"参数错误应失败：{result}")
        expect(result["observations"] == [], "参数错误不应产生观测")

    def test_max_steps_validation():
        try:
            core.build_graph(max_steps=0)
        except ValueError:
            return
        raise AssertionError("max_steps<1 应抛 ValueError")

    gate.check("01 固定工作流", test_fixed_workflow)
    gate.check("02 初始状态", test_initial_state)
    gate.check("03 正常有界循环", test_normal_loop)
    gate.check("04 预算耗尽", test_budget)
    gate.check("05 工具白名单", test_unknown_tool)
    gate.check("06 planner 异常", test_planner_error)
    gate.check("07 参数错误", test_bad_params)
    gate.check("08 max_steps 校验", test_max_steps_validation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
