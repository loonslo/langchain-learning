"""L6.2 LoRA 质量门禁 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l62", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l62"] = module
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
            "gate": "L6.2-lora-gate",
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

    def test_pass():
        result = core.quality_gate(0.3, 0.8)
        expect(result["passed"] is True and result["reasons"] == [], f"应通过：{result}")

    def test_low_adapter():
        result = core.quality_gate(0.3, 0.7)
        expect(result["passed"] is False and result["reasons"], f"适配器分低应拒绝：{result}")

    def test_low_gain():
        result = core.quality_gate(0.8, 0.9)
        expect(result["passed"] is False and result["reasons"], f"增益不足应拒绝：{result}")

    def test_invalid_scores():
        for base, adapter in ((-0.1, 0.8), (0.2, 1.1)):
            try:
                core.quality_gate(base, adapter)
            except ValueError:
                continue
            raise AssertionError("得分越界应报错")

    def test_config():
        expect(core.validate_training_config(0.0002, 3, 8, 16) == (), "合法超参不应报错")
        errors = core.validate_training_config(5e-5, 0, 0, 0)
        expect(len(errors) == 4, f"应报 4 项：{errors}")

    gate.check("01 通过", test_pass)
    gate.check("02 适配器分低", test_low_adapter)
    gate.check("03 增益不足", test_low_gain)
    gate.check("04 得分越界", test_invalid_scores)
    gate.check("05 超参校验", test_config)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
