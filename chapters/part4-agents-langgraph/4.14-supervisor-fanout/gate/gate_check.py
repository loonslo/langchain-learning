"""L4.9 Supervisor 与并行 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l414", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l414"] = module
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
            "gate": "L4.9-supervisor",
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

    def test_pipeline():
        expect(core.next_stage("") == "research", "空阶段应 research")
        expect(core.next_stage("research") == "writing", "research 应 writing")
        expect(core.next_stage("writing") == "review", "writing 应 review")
        expect(core.next_stage("review") == "FINISH", "review 应 FINISH")

    def test_custom_pipeline():
        expect(core.next_stage("a", ["a", "b"]) == "b", "自定义流水线不对")
        expect(core.next_stage("b", ["a", "b"]) == "FINISH", "最后应 FINISH")

    def test_invalid_stage():
        try:
            core.next_stage("unknown")
        except ValueError:
            return
        raise AssertionError("未知阶段应抛 ValueError")

    def test_invalid_pipeline():
        for pipeline in ([], "research"):
            try:
                core.next_stage("", pipeline)  # type: ignore[arg-type]
            except ValueError:
                continue
            raise AssertionError("非法 pipeline 应抛 ValueError")

    def test_fan_in():
        expect(core.fan_in([["a", "b"], ["b", "c"], ["a"]]) == ["a", "b", "c"], "展平/去重保序不对")
        expect(core.fan_in([]) == [], "空输入应返回 []")
        try:
            core.fan_in("bad")  # type: ignore[arg-type]
        except ValueError:
            return
        raise AssertionError("非 list 应抛 ValueError")

    gate.check("01 固定流水线", test_pipeline)
    gate.check("02 自定义流水线", test_custom_pipeline)
    gate.check("03 未知阶段", test_invalid_stage)
    gate.check("04 非法 pipeline", test_invalid_pipeline)
    gate.check("05 fan-in 合并", test_fan_in)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
