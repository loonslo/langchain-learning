"""L5.3 扩展 · 向量库选型 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l98", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l98"] = module
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
            "gate": "L5.3-vectorstore",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def req(**overrides) -> dict:
    base = {
        "relational_transactions": False,
        "filtered_multitenancy": False,
        "dedicated_vector_service": False,
        "kubernetes_platform": False,
        "very_large_scale": False,
    }
    base.update(overrides)
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_milvus():
        expect(core.choose_vector_backend(req(very_large_scale=True, kubernetes_platform=True)) == "milvus", "大规模+K8s 应 Milvus")
        expect(core.choose_vector_backend(req(very_large_scale=True)) == "pgvector", "仅大规模不够 Milvus")

    def test_pgvector():
        expect(core.choose_vector_backend(req(relational_transactions=True)) == "pgvector", "事务需求应 pgvector")
        expect(core.choose_vector_backend(req()) == "pgvector", "默认应 pgvector")

    def test_qdrant():
        expect(core.choose_vector_backend(req(filtered_multitenancy=True)) == "qdrant", "租户过滤应 qdrant")
        expect(core.choose_vector_backend(req(dedicated_vector_service=True)) == "qdrant", "独立服务应 qdrant")
        expect(core.choose_vector_backend(req(relational_transactions=True, dedicated_vector_service=True)) == "qdrant", "独立服务优先于事务")

    def test_filter():
        expect(core.tenant_filter("t1")["must"][0]["match"]["value"] == "t1", "租户过滤不对")
        try:
            core.tenant_filter("")
        except ValueError:
            return
        raise AssertionError("空 tenant_id 应报错")

    gate.check("01 大规模+K8s", test_milvus)
    gate.check("02 事务/默认", test_pgvector)
    gate.check("03 租户/独立服务", test_qdrant)
    gate.check("04 租户过滤", test_filter)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
