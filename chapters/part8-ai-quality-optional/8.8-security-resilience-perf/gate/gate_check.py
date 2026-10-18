"""L8 安全/韧性/性能 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l88", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l88"] = module
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
            "gate": "L8-resilience",
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

    def test_success():
        result = core.call_with_retry(lambda: "ok", max_attempts=3)
        expect(result["result"] == "ok" and result["attempts"] == 1 and result["error"] is None, f"成功结果不对：{result}")

    def test_retry_then_success():
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise TimeoutError("x")
            return "ok"

        result = core.call_with_retry(flaky, max_attempts=3, sleep=lambda _s: None)
        expect(result["result"] == "ok" and result["attempts"] == 3, f"应第 3 次成功：{result}")

    def test_all_fail():
        waits = []

        def boom():
            raise ConnectionError("down")

        result = core.call_with_retry(boom, max_attempts=3, backoff_seconds=1.0, sleep=waits.append)
        expect(result["result"] is None and result["attempts"] == 3 and isinstance(result["error"], ConnectionError), f"失败结果不对：{result}")
        expect(waits == [1.0, 2.0], f"退避不对：{waits}")

    def test_retry_invalid():
        for args in ((0, 0.0), (3, -1.0)):
            try:
                core.call_with_retry(lambda: "x", args[0], args[1])
            except ValueError:
                continue
            raise AssertionError("非法重试参数应报错")

    def test_input():
        expect(core.validate_input("正常") == [], "正常输入不应报错")
        expect(core.validate_input("  "), "空白应报错")
        expect(core.validate_input("x" * 501), "超长应报错")
        expect(core.validate_input("a\x00b"), "控制字符应报错")
        expect(core.validate_input("a\nb\tc") == [], "换行/制表符应允许")

    def test_percentile_slo():
        expect(core.percentile([100, 200], 0.95) == 200, "p95 应取最大值")
        expect(core.percentile([100, 200], 0.5) == 100, "p50 不对")
        expect(core.meets_slo([100, 200], 0.01, 200, 0.05) is True, "SLO 应通过")
        expect(core.meets_slo([100, 300], 0.01, 200, 0.05) is False, "p95 超限应失败")
        try:
            core.meets_slo([], 0, 200, 0.05)
        except ValueError:
            return
        raise AssertionError("空样本应报错")

    gate.check("01 首次成功", test_success)
    gate.check("02 重试后成功", test_retry_then_success)
    gate.check("03 全部失败/退避", test_all_fail)
    gate.check("04 重试参数", test_retry_invalid)
    gate.check("05 输入校验", test_input)
    gate.check("06 分位数/SLO", test_percentile_slo)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
