"""L5.7 扩展 · Postgres RLS 仓储 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []
        self.closed = False

    def execute(self, query, params=()):
        self.calls.append((query, params))
        return self

    def fetchall(self):
        return list(self.rows)

    def close(self):
        self.closed = True


class FakeConn:
    def __init__(self, rows=None):
        self.cursor_obj = FakeCursor(rows)
        self.commits = 0
        self.cursor_calls = 0

    def cursor(self):
        self.cursor_calls += 1
        return self.cursor_obj

    def commit(self):
        self.commits += 1


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l95", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l95"] = module
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
            "gate": "L5.7-postgres-rls",
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

    def test_history_tenant():
        conn = FakeConn(rows=[("assistant", "a2"), ("user", "q1")])
        rows = core.PostgresConversationStore(conn).history(tenant_id="t1", user_id="u1", session_id="s1")
        expect([r["content"] for r in rows] == ["q1", "a2"], f"应旧->新：{rows}")
        sql = conn.cursor_obj.calls[0]
        expect("set_config" in sql[0] and sql[1] == ("t1",), f"应先设租户：{sql}")
        query, params = conn.cursor_obj.calls[1]
        for token in ("tenant_id", "user_id", "session_id"):
            expect(token in query, f"SQL 缺 {token}")
        expect(params[:3] == ("t1", "u1", "s1"), f"参数不对：{params}")
        expect(conn.commits == 1 and conn.cursor_obj.closed, "读完应 commit + close")

    def test_limit():
        store = core.PostgresConversationStore(FakeConn())
        for limit in (0, 101):
            try:
                store.history(tenant_id="t", user_id="u", session_id="s", limit=limit)
            except ValueError:
                continue
            raise AssertionError("limit 越界应报错")

    def test_append():
        conn = FakeConn()
        store = core.PostgresConversationStore(conn)
        store.append(tenant_id="t1", user_id="u1", session_id="s1", message={"role": "user", "content": "hi"})
        insert = conn.cursor_obj.calls[1]
        expect("INSERT" in insert[0] and insert[1][:3] == ("t1", "u1", "s1"), f"INSERT 参数不对：{insert}")
        expect(conn.commits == 1 and conn.cursor_obj.closed, "写完应 commit + close")

    def test_role():
        store = core.PostgresConversationStore(FakeConn())
        try:
            store.append(tenant_id="t", user_id="u", session_id="s", message={"role": "system", "content": "x"})
        except ValueError:
            return
        raise AssertionError("非法 role 应报错")

    gate.check("01 查询租户与顺序", test_history_tenant)
    gate.check("02 limit 边界", test_limit)
    gate.check("03 写入参数/提交", test_append)
    gate.check("04 role 校验", test_role)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
