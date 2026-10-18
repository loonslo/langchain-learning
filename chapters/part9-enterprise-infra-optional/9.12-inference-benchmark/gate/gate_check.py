"""L5.8 扩展 · 推理基准 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l912", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l912"] = module
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
            "gate": "L5.8-benchmark",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def sample(latency, ttft, tokens, success=True) -> dict:
    return {"latency_ms": latency, "ttft_ms": ttft, "output_tokens": tokens, "success": success}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_percentile():
        expect(core.percentile([100, 200], 0.95) == 200, "p95 应保留尾延迟")
        expect(core.percentile([100, 200], 0.5) == 100, "p50 nearest-rank 不对")
        for args in (([], 0.5), ([1], 1.1), ([1], -0.1)):
            try:
                core.percentile(*args)
            except ValueError:
                continue
            raise AssertionError(f"非法参数应报错：{args}")

    def test_summary():
        summary = core.summarize([sample(100, 10, 10), sample(200, 20, 10), sample(300, 30, 10), sample(400, 40, 10, False)])
        expect(summary["p50_latency_ms"] == 200, f"p50 不对：{summary}")
        expect(summary["p95_latency_ms"] == 300, f"p95 应只看成功：{summary}")
        expect(summary["p95_ttft_ms"] == 30, f"p95 TTFT 不对：{summary}")
        expect(abs(summary["output_tokens_per_second"] - 50) < 1e-9, f"吞吐不对：{summary}")
        expect(summary["error_rate"] == 0.25, f"错误率不对：{summary}")

    def test_errors():
        for samples in ([], [sample(1, 1, 1, False)]):
            try:
                core.summarize(samples)
            except ValueError:
                continue
            raise AssertionError("空/无成功样本应报错")

    def test_release():
        summary = {"p95_latency_ms": 300, "p95_ttft_ms": 30, "error_rate": 0.25}
        slo = {"max_p95_latency_ms": 500, "max_p95_ttft_ms": 50, "max_error_rate": 0.3}
        expect(core.release_errors(summary, slo) == (), "未超限应放行")
        bad = {"p95_latency_ms": 600, "p95_ttft_ms": 60, "error_rate": 0.4}
        errors = core.release_errors(bad, slo)
        expect(len(errors) == 3, f"应报 3 项：{errors}")

    gate.check("01 分位数", test_percentile)
    gate.check("02 汇总", test_summary)
    gate.check("03 空/无成功样本", test_errors)
    gate.check("04 发布门禁", test_release)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
