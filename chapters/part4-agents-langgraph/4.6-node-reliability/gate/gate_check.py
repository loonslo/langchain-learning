"""L4.3 扩展 · 节点可靠性 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l46", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l46"] = module
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
            "gate": "L4.3-node-reliability",
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
        result = core.robust_call(lambda: "ok", "fallback")
        expect(result == {"ok": True, "value": "ok", "error": None}, f"成功结果不对：{result}")

    def test_fallback():
        def boom():
            raise ConnectionError("down")

        result = core.robust_call(boom, "fallback")
        expect(result["ok"] is False and result["value"] == "fallback", f"降级结果不对：{result}")
        expect("down" in result["error"], f"错误原因不对：{result}")

    def test_retryable():
        expect(core.is_retryable(TimeoutError()) is True, "TimeoutError 可重试")
        expect(core.is_retryable(ConnectionError()) is True, "ConnectionError 可重试")
        expect(core.is_retryable(ValueError()) is False, "ValueError 不可重试")
        expect(core.is_retryable(KeyError()) is False, "KeyError 不可重试")

    def test_timeout_fast():
        expect(core.with_timeout(lambda: "fast", 1.0, "fallback") == "fast", "快速调用应返回结果")

    def test_timeout_slow():
        start = time.monotonic()
        result = core.with_timeout(lambda: (time.sleep(0.1), "slow")[1], 0.02, "fallback")
        elapsed = time.monotonic() - start
        expect(result == "fallback", f"超时应降级：{result}")
        expect(elapsed < 0.5, f"不应无限等待：{elapsed:.2f}s")

    def test_invalid_seconds():
        for seconds in (0, -1):
            try:
                core.with_timeout(lambda: "x", seconds, "fallback")
            except ValueError:
                continue
            raise AssertionError("seconds<=0 应抛 ValueError")

    def test_fn_error_propagates():
        try:
            core.with_timeout(lambda: (_ for _ in ()).throw(ValueError("bad")), 1.0, "fallback")
        except ValueError:
            return
        raise AssertionError("fn 异常应原样抛出")

    gate.check("01 成功调用", test_success)
    gate.check("02 失败降级", test_fallback)
    gate.check("03 可重试判断", test_retryable)
    gate.check("04 快速调用", test_timeout_fast)
    gate.check("05 超时降级", test_timeout_slow)
    gate.check("06 非法 seconds", test_invalid_seconds)
    gate.check("07 fn 异常透传", test_fn_error_propagates)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
