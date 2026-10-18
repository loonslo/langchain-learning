"""L3.1 失败分析 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l31", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l31"] = module
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
            "gate": "L3.1-error-analysis",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def base(**overrides) -> dict:
    trace = {
        "case_id": "case",
        "source_available": True,
        "chunk_contains_fact": True,
        "expected_ids": ("refund-1",),
        "retrieved_ids": ("refund-1",),
        "ranked_ids": ("refund-1",),
        "context_ids": ("refund-1",),
        "cited_ids": ("refund-1",),
        "answer_correct": True,
        "should_refuse": False,
        "refused": False,
    }
    trace.update(overrides)
    return trace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def layer(trace: dict) -> str:
        return core.diagnose(trace)[0]

    def test_pass():
        expect(layer(base()) == "pass", "正常样本应 pass")

    def test_refusal():
        expect(layer(base(should_refuse=True, refused=False)) == "refusal", "应拒未拒应 refusal")
        expect(layer(base(should_refuse=True, refused=True, cited_ids=())) == "pass", "正确拒答应 pass")
        expect(layer(base(should_refuse=True, refused=True, cited_ids=("refund-1",))) == "citation", "拒答带引用应 citation")

    def test_labeling():
        expect(layer(base(expected_ids=())) == "labeling", "资料内无标注应 labeling")

    def test_source_and_chunking():
        expect(layer(base(source_available=False)) == "source", "来源缺失应 source")
        expect(layer(base(chunk_contains_fact=False)) == "chunking", "切分截断应 chunking")

    def test_retrieval_order():
        expect(layer(base(retrieved_ids=())) == "retrieval", "未召回应 retrieval")
        expect(layer(base(ranked_ids=())) == "reranking", "重排丢失应 reranking")
        expect(layer(base(context_ids=())) == "context", "上下文丢失应 context")

    def test_source_beats_downstream():
        expect(layer(base(source_available=False, retrieved_ids=())) == "source", "源头问题应优先")
        expect(layer(base(chunk_contains_fact=False, retrieved_ids=())) == "chunking", "切分应优先于召回")

    def test_generation():
        expect(layer(base(answer_correct=False)) == "generation", "证据齐全答错应 generation")
        expect(layer(base(refused=True)) == "generation", "证据齐全拒答应 generation")

    def test_citation():
        expect(layer(base(cited_ids=())) == "citation", "缺引用应 citation")
        expect(layer(base(cited_ids=("refund-1", "fake"))) == "citation", "引用上下文外 ID 应 citation")

    gate.check("01 正常通过", test_pass)
    gate.check("02 拒答与拒答引用", test_refusal)
    gate.check("03 缺少标注", test_labeling)
    gate.check("04 来源与切分", test_source_and_chunking)
    gate.check("05 召回/重排/上下文", test_retrieval_order)
    gate.check("06 源头优先于下游", test_source_beats_downstream)
    gate.check("07 生成失败", test_generation)
    gate.check("08 引用失败", test_citation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
