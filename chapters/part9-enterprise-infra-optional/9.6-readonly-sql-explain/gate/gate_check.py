"""L5.7 扩展 · 只读 SQL 护栏 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l96", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l96"] = module
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
            "gate": "L5.7-sql-guard",
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

    def test_valid():
        sql = "  SELECT id, name FROM users WHERE id = %s LIMIT 10 "
        result = core.validate_read_only_sql(sql, allowed_tables={"users"})
        expect(result == "SELECT id, name FROM users WHERE id = %s LIMIT 10", f"压缩/校验不对：{result}")

    def test_prefix():
        for sql in ("DELETE FROM users LIMIT 1", "select * from users limit 1; drop table users"):
            try:
                core.validate_read_only_sql(sql, allowed_tables={"users"})
            except core.SqlPolicyError:
                continue
            raise AssertionError(f"应拒绝：{sql}")

    def test_forbidden():
        for sql in ("select * from users for update limit 1", "select * from users limit 1 -- x", "insert into users values (1) limit 1"):
            try:
                core.validate_read_only_sql(sql, allowed_tables={"users"})
            except core.SqlPolicyError:
                continue
            raise AssertionError(f"应拒绝：{sql}")

    def test_table_limit():
        for sql in ("select * from secrets limit 1", "select * from users"):
            try:
                core.validate_read_only_sql(sql, allowed_tables={"users"})
            except core.SqlPolicyError:
                continue
            raise AssertionError(f"应拒绝：{sql}")

    def test_catalog():
        catalog = core.QueryCatalog(
            {"q1": {"sql": "select id from users limit 5", "allowed_roles": {"analyst"}}},
            allowed_tables={"users"},
        )
        expect(catalog.get("q1", ["analyst"]).lower().endswith("limit 5"), "目录取用不对")
        try:
            catalog.get("missing", ["analyst"])
        except core.SqlPolicyError:
            pass
        else:
            raise AssertionError("未知 id 应报错")
        try:
            catalog.get("q1", ["viewer"])
        except PermissionError:
            return
        raise AssertionError("角色不匹配应 PermissionError")

    def test_plan():
        good = [{"Plan": {"Node Type": "Index Scan", "Plan Rows": 10}}]
        core.reject_expensive_plan(good)
        bad = [{"Plan": {"Node Type": "Seq Scan", "Plan Rows": 200000}}]
        try:
            core.reject_expensive_plan(bad)
        except core.SqlPolicyError:
            pass
        else:
            raise AssertionError("超阈值顺扫应报错")
        try:
            core.reject_expensive_plan([])
        except core.SqlPolicyError:
            return
        raise AssertionError("无效 EXPLAIN 应报错")

    gate.check("01 合法查询", test_valid)
    gate.check("02 只读前缀/多语句", test_prefix)
    gate.check("03 禁止关键字/注释", test_forbidden)
    gate.check("04 表白名单/LIMIT", test_table_limit)
    gate.check("05 查询目录", test_catalog)
    gate.check("06 执行计划", test_plan)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
