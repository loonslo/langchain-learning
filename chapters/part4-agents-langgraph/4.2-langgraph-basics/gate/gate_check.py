"""L4.2 LangGraph 基础 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l42", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l42"] = module
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
            "gate": "L4.2-langgraph-basics",
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

    def test_linear():
        result = core.build_linear().invoke({"history": []})
        expect(result["history"] == ["step_a 完成", "step_b 完成"], f"线性历史不对：{result}")

    def test_conditional():
        result = core.build_conditional().invoke({"history": [], "attempts": 0, "approved": False})
        expect(result["attempts"] == 2, f"应循环 2 次：{result}")
        expect(result["approved"] is True, f"应通过：{result}")
        expect(result["history"].count("step_b 完成") == 2, f"step_b 应执行两次：{result['history']}")
        expect("step_c 校验：不通过" in result["history"], f"缺不通过记录：{result['history']}")
        expect("step_c 校验：通过" in result["history"], f"缺通过记录：{result['history']}")

    def test_conditional_initial_pass():
        result = core.build_conditional().invoke({"history": [], "attempts": 1, "approved": False})
        expect(result["attempts"] == 2 and result["approved"] is True, f"从 attempts=1 开始应再走一轮：{result}")

    def test_linear_no_side_effects():
        first = core.build_linear().invoke({"history": []})
        second = core.build_linear().invoke({"history": []})
        expect(first["history"] == second["history"], "线性图不应共享状态")

    gate.check("01 线性图顺序", test_linear)
    gate.check("02 分支循环与审批", test_conditional)
    gate.check("03 从 attempts=1 继续", test_conditional_initial_pass)
    gate.check("04 图之间状态隔离", test_linear_no_side_effects)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
