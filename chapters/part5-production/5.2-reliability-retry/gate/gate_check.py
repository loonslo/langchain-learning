"""L5.2 可靠性 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l52", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l52"] = module
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
            "gate": "L5.2-reliability",
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

    def test_backoff():
        expect(core.backoff_delays(3) == [1.0, 2.0, 4.0], "退避序列不对")
        expect(core.backoff_delays(0) == [], "0 次应为空")
        expect(core.backoff_delays(6, 1, 20) == [1, 2, 4, 8, 16, 20], "上限截断不对")

    def test_backoff_invalid():
        for args in ((-1, 1, 20), (3, 0, 20), (3, 1, 0)):
            try:
                core.backoff_delays(*args)
            except ValueError:
                continue
            raise AssertionError(f"非法参数应报错：{args}")

    def test_retryable():
        expect(core.is_retryable(TimeoutError()) is True, "Timeout 可重试")
        expect(core.is_retryable(ConnectionError()) is True, "Connection 可重试")
        for exc in (ValueError(), KeyError(), PermissionError()):
            expect(core.is_retryable(exc) is False, f"{type(exc).__name__} 不应重试")

    def test_cost():
        expect(core.estimate_cost({"total_tokens": 2000}, 0.001) == 0.002, "成本不对")
        expect(core.estimate_cost(None, 0.001) == 0.0, "None 应为 0")
        expect(core.estimate_cost({}, 0.001) == 0.0, "缺字段应为 0")

    def test_cost_invalid():
        try:
            core.estimate_cost({"total_tokens": 1}, -0.1)
        except ValueError:
            return
        raise AssertionError("负单价应抛 ValueError")

    gate.check("01 指数退避", test_backoff)
    gate.check("02 退避参数校验", test_backoff_invalid)
    gate.check("03 可重试判断", test_retryable)
    gate.check("04 成本估算", test_cost)
    gate.check("05 成本参数校验", test_cost_invalid)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
