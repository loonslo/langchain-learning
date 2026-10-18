"""L3.3 基础评测 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l32", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l32"] = module
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
            "gate": "L3.3-eval-basics",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


CASES = [
    {"id": "f1", "question": "q1", "keywords": ["检索", "生成"], "should_refuse": False},
    {"id": "f2", "question": "q2", "keywords": ["向量"], "should_refuse": False},
    {"id": "r1", "question": "q3", "keywords": [], "should_refuse": True},
    {"id": "r2", "question": "q4", "keywords": [], "should_refuse": True},
    {"id": "skip", "question": "q5", "keywords": [], "should_refuse": False},
]

ANSWERS = {
    "q1": "检索增强生成",
    "q2": "不知道",
    "q3": "我不知道",
    "q4": "这是答案",
    "q5": "任意回答",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def ask(question: str) -> str:
        return ANSWERS[question]

    def test_refuse_detection():
        expect(core.looks_like_refuse("文档中没有提到") is True, "应识别拒答")
        expect(core.looks_like_refuse("检索增强生成") is False, "正常答案不应拒答")
        for answer in (1, None):
            try:
                core.looks_like_refuse(answer)  # type: ignore[arg-type]
            except ValueError:
                continue
            raise AssertionError("非字符串应抛 ValueError")

    def test_metrics():
        report = core.evaluate(CASES, ask)
        expect(report["refusal_total"] == 2 and report["refusal_ok"] == 1, f"拒答指标不对：{report}")
        expect(report["keyword_total"] == 2 and report["keyword_ok"] == 1, f"关键词指标不对：{report}")
        expect(abs(report["refusal_accuracy"] - 0.5) < 1e-9, "拒答正确率不对")
        expect(abs(report["keyword_accuracy"] - 0.5) < 1e-9, "关键词命中率不对")

    def test_skip_without_keywords():
        report = core.evaluate([CASES[4]], ask)
        expect(report["keyword_total"] == 0 and report["keyword_accuracy"] == 0.0, f"无关键词应跳过：{report}")

    def test_empty():
        report = core.evaluate([], ask)
        expect(report["rows"] == [], "空集 rows 应为 []")
        expect(report["refusal_total"] == 0 and report["keyword_total"] == 0, "空集分母应为 0")

    def test_ask_error_counts():
        def broken(question: str) -> str:
            if question == "q2":
                raise TimeoutError("timeout")
            return ANSWERS[question]

        report = core.evaluate(CASES[:2], broken)
        expect(report["keyword_total"] == 2, "异常题仍应计入分母")
        expect(report["keyword_ok"] == 1, "异常题不应命中")
        expect(any(row.get("error") for row in report["rows"]), "异常行应有 error")

    def test_no_mutation():
        cases = [dict(row) for row in CASES]
        original = [dict(row) for row in cases]
        core.evaluate(cases, ask)
        expect(cases == original, "不应修改 eval_set")

    gate.check("01 拒答判断", test_refuse_detection)
    gate.check("02 拒答/关键词指标", test_metrics)
    gate.check("03 无关键词跳过", test_skip_without_keywords)
    gate.check("04 空评测集", test_empty)
    gate.check("05 ask_fn 异常", test_ask_error_counts)
    gate.check("06 不修改评测集", test_no_mutation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
