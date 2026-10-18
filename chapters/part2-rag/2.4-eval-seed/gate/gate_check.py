"""L2.9 RAG 评测基线 · 离线 gate 验收。

用法（仓库根目录）：
    python chapters/part2-rag/2.4-eval-seed/gate/gate_check.py
    python chapters/part2-rag/2.4-eval-seed/gate/gate_check.py --module 你的实现.py

默认检查同目录 starter.py。全部 PASS 时退出码为 0，并写出 gate_report.json。
不调用真实模型；固定结果由脚本注入，用来验证评测器能否抓住已知失败。
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
CASES_PATH = HERE / "cases.json"


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    sys.path.insert(0, str(CHAPTER))
    spec = importlib.util.spec_from_file_location("candidate_l29", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l29"] = module
    spec.loader.exec_module(module)
    return module


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float) -> bool:
    return abs(float(actual) - expected) < 1e-9


class Gate:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def check(self, name: str, fn) -> None:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - gate 要报告所有失败
            self.rows.append(
                {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
            )
        else:
            self.rows.append({"name": name, "ok": True, "error": ""})

    def report(self, module_path: Path) -> int:
        passed = sum(row["ok"] for row in self.rows)
        total = len(self.rows)
        for row in self.rows:
            mark = "PASS" if row["ok"] else "FAIL"
            suffix = "" if row["ok"] else f"  <- {row['error']}"
            print(f"[{mark}] {row['name']}{suffix}")
        print(f"\n{passed}/{total} passed")
        if passed != total:
            print("gate 未通过：先修 FAIL 项，不要打开参考实现。")
        out = {
            "gate": "L2.9-rag-eval-baseline",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return 0 if passed == total else 1


# 固定结果：每个问题对应一份“RAG 已经返回”的结果。
# 这些结果故意包含 6 个已知失败，gate 用它们验证评测器能不能抓住。
RESULTS = {
    "退款多久到账": {
        "answer": "退款审核通过后3个工作日到账。",
        "sources": ["refund-1"],
        "refused": False,
        "retrieved_ids": ["refund-1", "refund-2"],
    },
    "多久发货": {
        "answer": "付款后48小时内发货。",
        "sources": ["shipping-1"],
        "refused": False,
        "retrieved_ids": ["shipping-1"],
    },
    "退款和发货分别多久": {
        "answer": "退款3个工作日，发货48小时。",
        "sources": ["refund-1", "shipping-1"],
        "refused": False,
        "retrieved_ids": ["refund-1", "shipping-1"],
    },
    "量子纠缠是什么": {
        "answer": "文档中没有提到。",
        "sources": [],
        "refused": True,
        "retrieved_ids": [],
    },
    "   ": {
        "answer": "文档中没有提到。",
        "sources": [],
        "refused": True,
        "retrieved_ids": [],
    },
    "退款超过7天怎么办": {
        "answer": "退款超过7天请联系人工。",
        "sources": ["refund-2"],
        "refused": False,
        "retrieved_ids": ["refund-2"],
    },
    "退款多久": {
        "answer": "3个工作日。",
        "sources": ["refund-1"],
        "refused": False,
        "retrieved_ids": ["refund-1"],
    },
    "保修多久": {
        "answer": "保修1年，3个工作日。",
        "sources": ["fake-1"],
        "refused": False,
        "retrieved_ids": ["refund-1"],
    },
    "发货时间": {
        "answer": "48小时内发货。",
        "sources": [],
        "refused": False,
        "retrieved_ids": ["shipping-1"],
    },
    "股票走势": {
        "answer": "文档中没有提到。",
        "sources": ["refund-1"],
        "refused": True,
        "retrieved_ids": [],
    },
    "退款到账": {
        "answer": "文档中没有提到。",
        "sources": [],
        "refused": True,
        "retrieved_ids": ["refund-1"],
    },
    "退款规则": {
        "answer": "3个工作日，7天。",
        "sources": ["refund-1", "refund-1", "refund-2"],
        "refused": False,
        "retrieved_ids": ["refund-1", "refund-2"],
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def cases() -> list[dict]:
        return core.load_cases(CASES_PATH)

    def result(question: str) -> dict:
        return copy.deepcopy(RESULTS[question])

    def run_all() -> dict:
        return core.run(cases(), lambda question: result(question))

    def test_load_valid():
        rows = cases()
        expect(isinstance(rows, list) and len(rows) == 12, f"应读到 12 条，实际 {len(rows)}")
        expect(len({row["id"] for row in rows}) == 12, "ID 应唯一")

    def test_load_rejects_duplicate_ids():
        bad = [
            {"id": "x", "question": "q", "expected_chunks": [], "keywords": [], "should_refuse": True},
            {"id": "x", "question": "q2", "expected_chunks": [], "keywords": [], "should_refuse": True},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
            try:
                core.load_cases(path)
            except ValueError:
                return
        raise AssertionError("重复 ID 应抛 ValueError")

    def test_load_rejects_missing_keys():
        bad = [{"id": "x", "question": "q"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
            try:
                core.load_cases(path)
            except ValueError:
                return
        raise AssertionError("缺字段应抛 ValueError")

    def test_evaluate_passes_correct_case():
        row = core.evaluate_case(cases()[0], result("退款多久到账"))
        expect(row["id"] == "refund", f"id 不对：{row['id']}")
        expect(row["retrieval_hit"] is True, "应召回期望片段")
        expect(row["citation_ok"] is True, "引用应正确")
        expect(row["refusal_ok"] is True, "拒答判断应正确")
        expect(row["keyword_ok"] is True, "关键词应命中")
        expect(row["passed"] is True, "正确样本应通过")

    def test_evaluate_catches_retrieval_miss():
        row = core.evaluate_case(cases()[6], result("退款多久"))
        expect(row["retrieval_hit"] is False, "少召回一个片段应判 retrieval_hit=False")
        expect(row["passed"] is False, "召回缺失不应通过")

    def test_evaluate_catches_fabricated_citation():
        row = core.evaluate_case(cases()[7], result("保修多久"))
        expect(row["citation_ok"] is False, "引用不在召回集合中应判失败")
        expect(row["passed"] is False, "伪造引用不应通过")

    def test_evaluate_catches_missing_citation():
        row = core.evaluate_case(cases()[8], result("发货时间"))
        expect(row["citation_ok"] is False, "作答无引用应判失败")
        expect(row["passed"] is False, "无引用不应通过")

    def test_evaluate_catches_refusal_with_citation():
        row = core.evaluate_case(cases()[9], result("股票走势"))
        expect(row["citation_ok"] is False, "拒答附来源应判失败")
        expect(row["passed"] is False, "拒答附来源不应通过")

    def test_evaluate_catches_wrong_refusal():
        row = core.evaluate_case(cases()[10], result("退款到账"))
        expect(row["refusal_ok"] is False, "该答却拒答应判失败")
        expect(row["passed"] is False, "错误拒答不应通过")

    def test_evaluate_catches_duplicate_citation():
        row = core.evaluate_case(cases()[11], result("退款规则"))
        expect(row["citation_ok"] is False, "重复引用应判失败")
        expect(row["passed"] is False, "重复引用不应通过")

    def test_evaluate_rejects_missing_result_key():
        bad = result("退款多久到账")
        bad.pop("sources")
        try:
            core.evaluate_case(cases()[0], bad)
        except ValueError:
            return
        raise AssertionError("结果缺字段应抛 ValueError")

    def test_summary_metrics():
        report = run_all()
        summary = report["summary"]
        expect(summary["total"] == 12, f"total 不对：{summary['total']}")
        expect(summary["passed"] == 6, f"passed 应为 6，实际 {summary['passed']}")
        expect(close(summary["pass_rate"], 0.5), f"pass_rate 不对：{summary['pass_rate']}")
        expect(
            close(summary["retrieval_hit_rate"], 8 / 9),
            f"retrieval_hit_rate 不对：{summary['retrieval_hit_rate']}",
        )
        expect(
            close(summary["citation_accuracy"], 7 / 12),
            f"citation_accuracy 不对：{summary['citation_accuracy']}",
        )
        expect(
            close(summary["refusal_accuracy"], 11 / 12),
            f"refusal_accuracy 不对：{summary['refusal_accuracy']}",
        )

    def test_run_returns_rows_and_keeps_cases():
        original = copy.deepcopy(cases())
        report = run_all()
        expect(len(report["rows"]) == 12, "rows 数量不对")
        expect(report["rows"][0]["id"] == "refund", "rows 顺序应与 cases 一致")
        expect(cases() == original, "run 不应修改 cases")

    def test_run_handles_ask_exception():
        rows = cases()[:2]

        def flaky(question: str) -> dict:
            if question == "多久发货":
                raise TimeoutError("upstream timeout")
            return result(question)

        report = core.run(rows, flaky)
        expect(len(report["rows"]) == 2, "异常时也应保留该行")
        expect(report["rows"][1]["passed"] is False, "异常行不应通过")
        expect(report["rows"][1].get("error"), "异常行应记录可读错误")
        expect(report["summary"]["total"] == 2, "汇总应包含异常行")
        expect(close(report["summary"]["pass_rate"], 0.5), "一条通过一条异常，pass_rate 应为 0.5")

    gate.check("01 读取并校验 12 条样本", test_load_valid)
    gate.check("02 拒绝重复 ID", test_load_rejects_duplicate_ids)
    gate.check("03 拒绝缺字段样本", test_load_rejects_missing_keys)
    gate.check("04 正确样本通过", test_evaluate_passes_correct_case)
    gate.check("05 抓住召回缺失", test_evaluate_catches_retrieval_miss)
    gate.check("06 抓住伪造引用", test_evaluate_catches_fabricated_citation)
    gate.check("07 抓住无引用作答", test_evaluate_catches_missing_citation)
    gate.check("08 抓住拒答附来源", test_evaluate_catches_refusal_with_citation)
    gate.check("09 抓住错误拒答", test_evaluate_catches_wrong_refusal)
    gate.check("10 抓住重复引用", test_evaluate_catches_duplicate_citation)
    gate.check("11 拒绝缺字段结果", test_evaluate_rejects_missing_result_key)
    gate.check("12 汇总指标正确", test_summary_metrics)
    gate.check("13 run 不改输入并保持顺序", test_run_returns_rows_and_keeps_cases)
    gate.check("14 ask_fn 异常不中断整批", test_run_handles_ask_exception)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
