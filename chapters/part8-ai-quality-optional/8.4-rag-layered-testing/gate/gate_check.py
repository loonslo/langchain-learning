"""L3.1 扩展 · RAG 分层检索评测 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l84", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l84"] = module
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
            "gate": "L3.1-layered-rag",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def case(relevant, retrieved, cited=()) -> dict:
    return {"case_id": "c", "relevant_sources": list(relevant), "retrieved_sources": list(retrieved), "cited_sources": list(cited)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_basic():
        metrics = core.evaluate_retrieval([case(("a", "b"), ("a", "c", "a"), ("a",))])
        expect(metrics["recall_at_k"] == 0.5, f"recall 不对：{metrics}")
        expect(metrics["precision_at_k"] == 0.5, f"precision 不对：{metrics}")
        expect(metrics["mrr"] == 1.0, f"MRR 不对：{metrics}")
        expect(metrics["citation_coverage"] == 0.5, f"citation 不对：{metrics}")

    def test_rank():
        metrics = core.evaluate_retrieval([case(("a",), ("x", "a"))])
        expect(metrics["precision_at_k"] == 0.5, f"precision 不对：{metrics}")
        expect(metrics["mrr"] == 0.5, f"MRR 应为 1/2：{metrics}")

    def test_refusal():
        metrics = core.evaluate_retrieval([case((), ())])
        expect(metrics["recall_at_k"] == 1.0 and metrics["citation_coverage"] == 1.0, f"拒答 recall/citation 应为 1：{metrics}")
        expect(metrics["precision_at_k"] == 0.0 and metrics["mrr"] == 0.0, f"拒答 precision/MRR 应为 0：{metrics}")

    def test_k_truncation():
        metrics = core.evaluate_retrieval([case(("b",), ("a", "b"))], k=1)
        expect(metrics["recall_at_k"] == 0.0, f"k=1 应未命中：{metrics}")

    def test_average_and_empty():
        metrics = core.evaluate_retrieval([case(("a",), ("a",)), case(("b",), ("x",))])
        expect(metrics["recall_at_k"] == 0.5, f"平均 recall 不对：{metrics}")
        empty = core.evaluate_retrieval([])
        expect(empty["recall_at_k"] == 0.0 and empty["mrr"] == 0.0, f"空集应全 0：{empty}")

    def test_invalid_k():
        try:
            core.evaluate_retrieval([], k=0)
        except ValueError:
            return
        raise AssertionError("k<1 应报错")

    gate.check("01 基本指标", test_basic)
    gate.check("02 排名/去重", test_rank)
    gate.check("03 拒答样本", test_refusal)
    gate.check("04 k 截断", test_k_truncation)
    gate.check("05 平均/空集", test_average_and_empty)
    gate.check("06 k 校验", test_invalid_k)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
