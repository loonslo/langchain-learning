"""L3.6 回归对比 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFUSE = ["没有提到", "不知道", "无法回答", "信息不足"]


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l37", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l37"] = module
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
            "gate": "L3.6-regression",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def case(**overrides) -> dict:
    data = {
        "id": "c1",
        "reference": "检索增强生成",
        "keywords": ["检索", "生成"],
        "expected_sources": ["doc.txt"],
        "should_refuse": False,
    }
    data.update(overrides)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_percentile():
        expect(core.percentile([], 50) == 0.0, "空列表应为 0")
        expect(core.percentile([10], 99) == 10, "单值应返回自身")
        expect(core.percentile([0, 10], 50) == 5, "p50 应为 5")
        for pct in (-1, 101):
            try:
                core.percentile([1], pct)
            except ValueError:
                continue
            raise AssertionError("pct 越界应抛 ValueError")

    def test_score_pass():
        scores = core.score_case(case(), {"answer": "检索增强生成，来自 doc.txt"})
        expect(scores["keyword_score"] == 1.0, f"keyword 不对：{scores}")
        expect(scores["citation_score"] == 1.0, f"citation 不对：{scores}")
        expect(scores["refusal_ok"] == 1.0 and scores["passed"] is True, f"应通过：{scores}")

    def test_score_keyword_miss():
        scores = core.score_case(case(), {"answer": "向量库"})
        expect(scores["keyword_score"] < 0.67 and scores["passed"] is False, f"关键词未命中应失败：{scores}")

    def test_score_refusal():
        scores = core.score_case(case(should_refuse=True, keywords=[], expected_sources=[]), {"answer": "我不知道"})
        expect(scores["refusal_ok"] == 1.0 and scores["passed"] is True, f"正确拒答应通过：{scores}")
        scores = core.score_case(case(should_refuse=True, keywords=[], expected_sources=[]), {"answer": "这是答案"})
        expect(scores["refusal_ok"] == 0.0 and scores["passed"] is False, f"应拒未拒应失败：{scores}")

    def test_score_citation_miss():
        scores = core.score_case(case(), {"answer": "检索增强生成"})
        expect(scores["citation_score"] == 0.0 and scores["passed"] is False, f"缺来源应失败：{scores}")

    def test_summarize():
        rows = [
            {"latency_ms": 10, "runtime_error": "", "keyword_score": 1.0, "citation_score": 1.0, "refusal_ok": 1.0, "passed": True},
            {"latency_ms": 30, "runtime_error": "boom", "keyword_score": 0.0, "citation_score": 0.0, "refusal_ok": 0.0, "passed": False},
        ]
        summary = core.summarize(rows)
        expect(summary["cases"] == 2, f"cases 不对：{summary}")
        expect(summary["error_rate"] == 0.5, f"error_rate 不对：{summary}")
        expect(summary["p50_latency_ms"] == 20, f"p50 不对：{summary}")
        expect(abs(summary["p99_latency_ms"] - 29.8) < 1e-9, f"p99 不对：{summary}")
        expect(summary["pass_rate"] == 0.5 and summary["keyword_score"] == 0.5, f"汇总不对：{summary}")
        expect(len(summary["failures"]) == 1, "failures 不对")
        empty = core.summarize([])
        expect(empty["cases"] == 0 and empty["failures"] == [], f"空汇总不对：{empty}")

    def test_alerts():
        base = {"error_rate": 0.0, "p99_latency_ms": 1000, "pass_rate": 0.8, "citation_score": 0.9, "refusal_ok": 0.9}
        same = dict(base)
        expect(core.regression_alerts(base, same) == [], "无退化不应告警")
        worse = {"error_rate": 0.1, "p99_latency_ms": 3100, "pass_rate": 0.77, "citation_score": 0.87, "refusal_ok": 0.8}
        alerts = core.regression_alerts(base, worse)
        expect(len(alerts) == 5, f"应触发 5 条告警：{alerts}")

    def test_alert_boundary():
        base = {"error_rate": 0.0, "p99_latency_ms": 1000, "pass_rate": 0.8, "citation_score": 0.9, "refusal_ok": 0.9}
        edge = {"error_rate": 0.0, "p99_latency_ms": 3000, "pass_rate": 0.785, "citation_score": 0.885, "refusal_ok": 0.9}
        expect(core.regression_alerts(base, edge) == [], f"边界不应告警：{core.regression_alerts(base, edge)}")

    gate.check("01 分位数", test_percentile)
    gate.check("02 正确样本", test_score_pass)
    gate.check("03 关键词未命中", test_score_keyword_miss)
    gate.check("04 拒答评分", test_score_refusal)
    gate.check("05 来源缺失", test_score_citation_miss)
    gate.check("06 汇总指标", test_summarize)
    gate.check("07 回归告警", test_alerts)
    gate.check("08 告警边界", test_alert_boundary)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
