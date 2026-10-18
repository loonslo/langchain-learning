"""L2.2 向量化与召回 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l22", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l22"] = module
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
            "gate": "L2.2-embed-retrieve",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


VECTORS = {"a": [1.0, 0.0], "b": [0.0, 1.0], "c": [1.0, 1.0]}


def fake_embed(text: str) -> list[float]:
    return VECTORS[text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_cosine():
        expect(close(core.cosine([1, 0], [1, 0]), 1.0), "同向应为 1")
        expect(close(core.cosine([1, 0], [0, 1]), 0.0), "正交应为 0")
        expect(close(core.cosine([1, 0], [-1, 0]), -1.0), "反向应为 -1")
        expect(close(core.cosine([0, 0], [1, 0]), 0.0), "零向量应为 0")

    def test_cosine_errors():
        for a, b in (([], [1]), ([1, 0], [1]), ([1, 0], [1, 0, 0])):
            try:
                core.cosine(a, b)
            except ValueError:
                continue
            raise AssertionError(f"非法向量应抛 ValueError：{a}, {b}")

    def test_embed_texts():
        rows = core.embed_texts(["a", "b"], fake_embed)
        expect(rows == [VECTORS["a"], VECTORS["b"]], f"向量不对：{rows}")
        expect(core.embed_texts([], fake_embed) == [], "空输入应返回 []")

    def test_embed_errors():
        bad_fns = [
            lambda _t: [],
            lambda _t: "not list",
            lambda t: [1.0, 0.0] if t == "a" else [1.0, 0.0, 0.0],
        ]
        for fn in bad_fns:
            try:
                core.embed_texts(["a", "b"], fn)
            except ValueError:
                continue
            raise AssertionError("非法向量应抛 ValueError")
        try:
            core.embed_texts(["a", 1], fake_embed)  # type: ignore[list-item]
        except ValueError:
            return
        raise AssertionError("非字符串文本应抛 ValueError")

    def test_index_search():
        index = core.VectorIndex()
        index.add(["a", "b", "c"], [VECTORS["a"], VECTORS["b"], VECTORS["c"]])
        rows = index.search([1.0, 0.0], k=2)
        expect([row["id"] for row in rows] == ["a", "c"], f"排序不对：{rows}")
        expect(close(rows[0]["score"], 1.0), "a 分数应为 1")
        expect(close(rows[1]["score"], 1 / math.sqrt(2)), "c 分数不对")

    def test_index_empty_and_k():
        index = core.VectorIndex()
        expect(index.search([1.0, 0.0]) == [], "空索引应返回 []")
        index.add(["a"], [VECTORS["a"]])
        try:
            index.search([1.0, 0.0], k=0)
        except ValueError:
            return
        raise AssertionError("k=0 应抛 ValueError")

    def test_index_rejects_bad_add():
        index = core.VectorIndex()
        cases = [
            (["a"], []),
            (["a", "a"], [[1.0], [1.0]]),
            ([""], [[1.0]]),
            (["a", "b"], [[1.0], [1.0, 0.0]]),
        ]
        for ids, vectors in cases:
            try:
                index.add(ids, vectors)
            except ValueError:
                continue
            raise AssertionError(f"非法写入应抛 ValueError：{ids}, {vectors}")

    def test_index_dimension_mismatch():
        index = core.VectorIndex()
        index.add(["a"], [[1.0, 0.0]])
        try:
            index.search([1.0, 0.0, 0.0])
        except ValueError:
            return
        raise AssertionError("查询维度不一致应抛 ValueError")

    def test_index_no_mutation():
        ids = ["a"]
        vectors = [[1.0, 0.0]]
        index = core.VectorIndex()
        index.add(ids, vectors)
        ids.append("b")
        vectors[0][0] = 99.0
        rows = index.search([1.0, 0.0])
        expect(close(rows[0]["score"], 1.0), "索引不应被外部列表修改")

    gate.check("01 余弦相似度", test_cosine)
    gate.check("02 余弦非法输入", test_cosine_errors)
    gate.check("03 批量向量化", test_embed_texts)
    gate.check("04 向量化非法输入", test_embed_errors)
    gate.check("05 索引检索排序", test_index_search)
    gate.check("06 空索引与 k 校验", test_index_empty_and_k)
    gate.check("07 拒绝非法写入", test_index_rejects_bad_add)
    gate.check("08 查询维度不一致", test_index_dimension_mismatch)
    gate.check("09 不持有外部引用", test_index_no_mutation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
