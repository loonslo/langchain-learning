"""L5.4 数据持久化 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l54", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l54"] = module
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
            "gate": "L5.4-sqlite",
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

    def test_init():
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.db"
            expect(core.init_db(path) == 1, "schema 版本应为 1")
            expect(core.init_db(path) == 1, "init_db 应幂等")
            conn = sqlite3.connect(path)
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            conn.close()
            expect({"conversations", "feedback"} <= tables, f"缺表：{tables}")

    def test_save_history():
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.db"
            core.init_db(path)
            first = core.save_qa(path, "t1", "u1", "q1", "a1")
            core.save_qa(path, "t2", "u1", "q2", "a2")
            core.save_qa(path, "t3", "u2", "q3", "a3")
            rows = core.get_history(path, "u1")
            expect([r["question"] for r in rows] == ["q2", "q1"], f"历史顺序不对：{rows}")
            expect(isinstance(rows[0]["sources"], list), "sources 应还原为 list")
            expect("+00:00" in rows[0]["created_at"], f"created_at 应为 UTC ISO：{rows[0]}")
            page = core.get_history(path, "u1", limit=1, before_id=first + 1)
            expect([r["question"] for r in page] == ["q1"], f"游标分页不对：{page}")

    def test_idempotent():
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.db"
            core.init_db(path)
            a = core.save_qa(path, "same", "u1", "q", "a")
            b = core.save_qa(path, "same", "u1", "q", "a")
            expect(a == b, f"重复 trace 应返回同一 id：{a}, {b}")
            expect(len(core.get_history(path, "u1")) == 1, "重复写入不应新增记录")

    def test_feedback():
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.db"
            core.init_db(path)
            cid = core.save_qa(path, "t1", "u1", "q", "a")
            expect(core.save_feedback(path, cid, -1, "bad") > 0, "反馈应写入")
            try:
                core.save_feedback(path, cid, 0)
            except ValueError:
                pass
            else:
                raise AssertionError("rating=0 应抛 ValueError")
            try:
                core.save_feedback(path, 99999, 1)
            except ValueError:
                return
        raise AssertionError("不存在的会话应抛 ValueError")

    gate.check("01 建表与幂等", test_init)
    gate.check("02 写入/历史/分页", test_save_history)
    gate.check("03 trace 幂等", test_idempotent)
    gate.check("04 反馈校验", test_feedback)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
