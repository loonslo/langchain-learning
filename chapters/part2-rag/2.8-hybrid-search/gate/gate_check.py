"""L2.5 混合检索 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l28", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l28"] = module
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
            "gate": "L2.5-hybrid-search",
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

    def test_rrf_basic():
        rows = core.rrf_fuse([["a", "b"], ["b", "a"]], k=60)
        expect([row["id"] for row in rows] == ["a", "b"], f"同分应按首次出现：{rows}")
        expect(close(rows[0]["score"], 1 / 61 + 1 / 62), f"分数不对：{rows[0]['score']}")

    def test_rrf_weights():
        rows = core.rrf_fuse([["a", "b"], ["b", "a"]], k=60, weights=[1.0, 0.0])
        expect([row["id"] for row in rows] == ["a", "b"], f"权重方向不对：{rows}")
        rows = core.rrf_fuse([["a", "b"], ["b", "a"]], k=60, weights=[0.0, 1.0])
        expect([row["id"] for row in rows] == ["b", "a"], f"权重方向不对：{rows}")

    def test_rrf_dedupe():
        rows = core.rrf_fuse([["a", "a", "b"]], k=60)
        expect([row["id"] for row in rows] == ["a", "b"], f"同路重复应只计一次：{rows}")
        expect(close(rows[0]["score"], 1 / 61), f"a 分数不对：{rows[0]['score']}")
        expect(close(rows[1]["score"], 1 / 63), f"b 分数不对：{rows[1]['score']}")

    def test_rrf_empty():
        expect(core.rrf_fuse([]) == [], "空 rankings 应返回 []")
        expect(core.rrf_fuse([[], []]) == [], "全空排序应返回 []")

    def test_rrf_errors():
        for kwargs in ({"k": 0}, {"weights": [1.0]}, {"weights": [-1.0, 1.0]}):
            try:
                core.rrf_fuse([["a"], ["b"]], **kwargs)
            except ValueError:
                continue
            raise AssertionError(f"非法参数应抛 ValueError：{kwargs}")

    def test_hybrid_basic():
        rows = core.hybrid_search(["a"], ["b"], k=1)
        expect(len(rows) == 1 and rows[0]["id"] == "a", f"top1 不对：{rows}")
        expect(close(rows[0]["score"], 0.5 / 61), f"分数不对：{rows[0]['score']}")

    def test_hybrid_empty_and_k():
        expect(core.hybrid_search([], []) == [], "两路空应返回 []")
        try:
            core.hybrid_search(["a"], ["b"], k=0)
        except ValueError:
            return
        raise AssertionError("k=0 应抛 ValueError")

    gate.check("01 RRF 基本公式", test_rrf_basic)
    gate.check("02 权重方向", test_rrf_weights)
    gate.check("03 同路去重", test_rrf_dedupe)
    gate.check("04 空输入", test_rrf_empty)
    gate.check("05 非法参数", test_rrf_errors)
    gate.check("06 混合 top-k", test_hybrid_basic)
    gate.check("07 空结果与 k 校验", test_hybrid_empty_and_k)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
