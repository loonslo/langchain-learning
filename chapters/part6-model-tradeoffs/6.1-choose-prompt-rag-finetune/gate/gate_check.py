"""L6.1 方案选型 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l61", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l61"] = module
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
            "gate": "L5.10-model-strategy",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def args(**overrides) -> dict:
    base = {
        "knowledge_updates_often": False,
        "need_citation": False,
        "model_lacks_required_knowledge": False,
        "need_fixed_behavior": False,
        "enough_training_examples": False,
        "training_is_feasible": False,
    }
    base.update(overrides)
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args_ = parser.parse_args()
    module_path = Path(args_.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_prompt():
        result = core.decide(**args())
        expect(result["strategy"] == "Prompt", f"应 Prompt：{result}")
        expect(len(result["production_checks"]) >= 3, f"检查项不足：{result}")

    def test_rag():
        for key in ("knowledge_updates_often", "need_citation", "model_lacks_required_knowledge"):
            result = core.decide(**args(**{key: True}))
            expect(result["strategy"] == "RAG", f"{key}=True 应 RAG：{result}")

    def test_finetune():
        result = core.decide(**args(need_fixed_behavior=True, enough_training_examples=True, training_is_feasible=True))
        expect(result["strategy"] == "微调", f"应微调：{result}")
        expect(any("基座" in item for item in result["production_checks"]), f"缺基座对照：{result}")

    def test_both():
        result = core.decide(**args(
            knowledge_updates_often=True, need_fixed_behavior=True,
            enough_training_examples=True, training_is_feasible=True,
        ))
        expect(result["strategy"] == "RAG + 微调", f"应组合：{result}")

    def test_missing_prereq():
        result = core.decide(**args(need_fixed_behavior=True, enough_training_examples=True, training_is_feasible=False))
        expect(result["strategy"] == "Prompt", f"训练不可行不应微调：{result}")

    def test_recommend():
        text = core.recommend(True, True, False, False)
        expect(text.startswith("RAG："), f"简化建议不对：{text}")
        text = core.recommend(False, False, True, True, True)
        expect(text.startswith("微调："), f"简化建议不对：{text}")

    gate.check("01 默认 Prompt", test_prompt)
    gate.check("02 三种检索触发", test_rag)
    gate.check("03 微调前提", test_finetune)
    gate.check("04 组合方案", test_both)
    gate.check("05 缺训练条件", test_missing_prereq)
    gate.check("06 简化建议", test_recommend)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
