"""L2.8 重排与多模态 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l211", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l211"] = module
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
            "gate": "L2.8-rerank",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


DOCS = [
    {"id": "a", "text": "低相关"},
    {"id": "b", "text": "高相关"},
    {"id": "c", "text": "中相关"},
]
SCORES = {"低相关": 0.2, "高相关": 0.9, "中相关": 0.5}


def score(_query: str, text: str) -> float:
    return SCORES[text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_rerank_order():
        rows = core.rerank("q", DOCS, score, top_k=2)
        expect([row["id"] for row in rows] == ["b", "c"], f"排序/top_k 不对：{rows}")
        expect(rows[0]["score"] == 0.9, f"score 不对：{rows[0]}")

    def test_rerank_stable_tie():
        docs = [{"id": "x", "text": "x"}, {"id": "y", "text": "y"}]
        rows = core.rerank("q", docs, lambda q, t: 0.5)
        expect([row["id"] for row in rows] == ["x", "y"], f"同分应稳定：{rows}")

    def test_rerank_empty():
        expect(core.rerank("q", [], score) == [], "空 docs 应返回 []")

    def test_rerank_errors():
        for docs, top_k in (([{"id": "a"}], 3), ([{"id": "a", "text": 1}], 3), (DOCS, 0)):
            try:
                core.rerank("q", docs, score, top_k=top_k)
            except ValueError:
                continue
            raise AssertionError(f"非法输入应抛 ValueError：{docs}, {top_k}")

    def test_rerank_bad_score():
        for fn in (lambda q, t: "bad", lambda q, t: (_ for _ in ()).throw(RuntimeError("down"))):
            try:
                core.rerank("q", DOCS, fn)
            except ValueError:
                continue
            raise AssertionError("非法 score 应抛 ValueError")

    def test_rerank_no_mutation():
        docs = [dict(row) for row in DOCS]
        original = [dict(row) for row in docs]
        core.rerank("q", docs, score)
        expect(docs == original, "不应修改输入")

    def test_recall():
        expect(core.recall_at_k(["a", "b", "c"], ["a", "c"], 2) == 0.5, "recall@2 不对")
        expect(core.recall_at_k(["a", "b", "c"], ["a", "c"], 3) == 1.0, "recall@3 不对")
        expect(core.recall_at_k([], ["a"], 3) == 0.0, "空结果应为 0")
        expect(core.recall_at_k(["a"], [], 3) == 0.0, "无相关 ID 应为 0")

    def test_recall_k():
        try:
            core.recall_at_k(["a"], ["a"], 0)
        except ValueError:
            return
        raise AssertionError("k=0 应抛 ValueError")

    gate.check("01 重排顺序与 top-k", test_rerank_order)
    gate.check("02 同分稳定", test_rerank_stable_tie)
    gate.check("03 空候选", test_rerank_empty)
    gate.check("04 非法候选/top_k", test_rerank_errors)
    gate.check("05 非法 score", test_rerank_bad_score)
    gate.check("06 不修改输入", test_rerank_no_mutation)
    gate.check("07 recall@k", test_recall)
    gate.check("08 recall k 校验", test_recall_k)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
