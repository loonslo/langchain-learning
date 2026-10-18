"""L4.5 扩展 · 规划与执行 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l48", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l48"] = module
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
            "gate": "L4.5-plan-execute",
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

    def plan(_task: str) -> list[str]:
        return ["第一步", "第二步", "第三步"]

    def execute(_task: str, step: str) -> str:
        return f"完成：{step}"

    def test_parse():
        text = "1. 第一步\n2) 第二步\n- 第三步\n第三步\n"
        steps = core.parse_plan(text)
        expect(steps == ["第一步", "第二步", "第三步"], f"解析不对：{steps}")

    def test_parse_bounds():
        for text in ("只有一步", "a\nb\nc\nd\ne"):
            try:
                core.parse_plan(text)
            except ValueError:
                continue
            raise AssertionError(f"步数越界应抛 ValueError：{text!r}")
        try:
            core.parse_plan(123)  # type: ignore[arg-type]
        except ValueError:
            return
        raise AssertionError("非字符串应抛 ValueError")

    def test_run_normal():
        result = core.run_plan("任务", plan, execute)
        expect(result["plan"] == ["第一步", "第二步", "第三步"], f"计划不对：{result}")
        expect(result["results"] == ["完成：第一步", "完成：第二步", "完成：第三步"], f"结果不对：{result}")
        expect(result["error"] is None, f"error 应为 None：{result}")

    def test_run_errors():
        def bad_plan(_task):
            raise RuntimeError("planner down")

        def bad_execute(_task, _step):
            raise RuntimeError("executor down")

        expect(core.run_plan("任务", bad_plan, execute)["error"] == "plan_error", "计划异常应 plan_error")
        expect(core.run_plan("任务", plan, bad_execute)["error"] == "execute_error", "执行异常应 execute_error")
        for args in (("", plan, execute), ("任务", plan, execute)):
            if args[0] == "":
                try:
                    core.run_plan(*args)
                except ValueError:
                    continue
                raise AssertionError("空任务应抛 ValueError")

    def test_plan_too_long():
        result = core.run_plan("任务", plan, execute, max_steps=2)
        expect(result["results"] == ["完成：第一步", "完成：第二步"], f"应只执行 2 步：{result}")
        expect(result["error"] == "plan_too_long", f"error 不对：{result}")

    def test_validation():
        try:
            core.run_plan("任务", plan, execute, max_steps=0)
        except ValueError:
            return
        raise AssertionError("max_steps=0 应抛 ValueError")

    gate.check("01 计划解析", test_parse)
    gate.check("02 计划步数/类型校验", test_parse_bounds)
    gate.check("03 正常规划执行", test_run_normal)
    gate.check("04 计划/执行异常", test_run_errors)
    gate.check("05 计划过长截断", test_plan_too_long)
    gate.check("06 max_steps 校验", test_validation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
