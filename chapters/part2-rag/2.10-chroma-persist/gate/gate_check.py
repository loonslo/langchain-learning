"""L2.7 向量库持久化 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l210", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l210"] = module
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
            "gate": "L2.7-persistence",
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

    def make_store(tmp: str):
        return core.PersistentVectorStore(Path(tmp) / "store.json")

    def test_add_search():
        with tempfile.TemporaryDirectory() as tmp:
            store = make_store(tmp)
            store.add(["a", "b", "c"], [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], [{"x": 1}, {"x": 2}, {"x": 3}])
            rows = store.search([1.0, 0.0], k=2)
            expect([row["id"] for row in rows] == ["a", "c"], f"排序不对：{rows}")
            expect(rows[0]["metadata"] == {"x": 1}, f"metadata 不对：{rows[0]}")

    def test_save_load_roundtrip():
        with tempfile.TemporaryDirectory() as tmp:
            store = make_store(tmp)
            store.add(["a", "b"], [[1.0, 0.0], [0.0, 1.0]], [{"x": 1}, {"x": 2}])
            store.save()
            expect(store.path.is_file(), "save 应生成文件")
            loaded = core.PersistentVectorStore.load(store.path)
            rows = loaded.search([1.0, 0.0], k=2)
            expect([row["id"] for row in rows] == ["a", "b"], f"加载后排序不对：{rows}")
            expect(rows[0]["metadata"] == {"x": 1}, "加载后 metadata 丢失")

    def test_load_missing():
        with tempfile.TemporaryDirectory() as tmp:
            try:
                core.PersistentVectorStore.load(Path(tmp) / "missing.json")
            except core.StoreError:
                return
        raise AssertionError("缺文件应抛 StoreError")

    def test_load_corrupt():
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{not json", encoding="utf-8")
            try:
                core.PersistentVectorStore.load(path)
            except core.StoreError:
                return
        raise AssertionError("非法 JSON 应抛 StoreError")

    def test_duplicate_id():
        with tempfile.TemporaryDirectory() as tmp:
            store = make_store(tmp)
            store.add(["a"], [[1.0]])
            for ids in (["a"], ["b", "b"]):
                try:
                    store.add(ids, [[1.0]] * len(ids))
                except core.StoreError:
                    continue
                raise AssertionError(f"重复 ID 应抛 StoreError：{ids}")

    def test_dimension_and_metadata_errors():
        with tempfile.TemporaryDirectory() as tmp:
            store = make_store(tmp)
            cases = [
                (["a", "b"], [[1.0], [1.0, 0.0]], None),
                (["a"], [[1.0]], [{"x": 1}, {"x": 2}]),
            ]
            for ids, vectors, metadata in cases:
                try:
                    store.add(ids, vectors, metadata)
                except core.StoreError:
                    continue
                raise AssertionError(f"非法写入应抛 StoreError：{ids}, {vectors}, {metadata}")

    def test_empty_and_k():
        with tempfile.TemporaryDirectory() as tmp:
            store = make_store(tmp)
            expect(store.search([1.0]) == [], "空库应返回 []")
            store.add(["a"], [[1.0]])
            try:
                store.search([1.0], k=0)
            except core.StoreError:
                return
        raise AssertionError("k=0 应抛 StoreError")

    def test_query_dimension():
        with tempfile.TemporaryDirectory() as tmp:
            store = make_store(tmp)
            store.add(["a"], [[1.0, 0.0]])
            try:
                store.search([1.0])
            except core.StoreError:
                return
        raise AssertionError("查询维度不一致应抛 StoreError")

    def test_no_external_mutation():
        with tempfile.TemporaryDirectory() as tmp:
            store = make_store(tmp)
            ids = ["a"]
            vectors = [[1.0, 0.0]]
            metadata = [{"x": 1}]
            store.add(ids, vectors, metadata)
            vectors[0][0] = 99.0
            metadata[0]["x"] = 99
            rows = store.search([1.0, 0.0])
            expect(close(rows[0]["score"], 1.0), "索引不应被外部向量修改")
            expect(rows[0]["metadata"] == {"x": 1}, "索引不应被外部 metadata 修改")

    gate.check("01 写入与检索", test_add_search)
    gate.check("02 保存/加载往返", test_save_load_roundtrip)
    gate.check("03 拒绝缺失文件", test_load_missing)
    gate.check("04 拒绝非法 JSON", test_load_corrupt)
    gate.check("05 拒绝重复 ID", test_duplicate_id)
    gate.check("06 维度/metadata 错误", test_dimension_and_metadata_errors)
    gate.check("07 空库与 k 校验", test_empty_and_k)
    gate.check("08 查询维度不一致", test_query_dimension)
    gate.check("09 不持有外部引用", test_no_external_mutation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
