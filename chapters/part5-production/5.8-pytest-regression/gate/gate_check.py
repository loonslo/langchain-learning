"""L5.6 pytest 回归 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l58", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l58"] = module
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
            "gate": "L5.6-pytest-regression",
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

    def test_norm():
        expect(core.normalize("  ＲＡＧ  是 什么 ") == "rag是什么", "归一化不对")
        try:
            core.normalize(1)  # type: ignore[arg-type]
        except ValueError:
            return
        raise AssertionError("非字符串应抛 ValueError")

    def test_refused():
        expect(core.refused("文档中没有提到相关内容") is True, "应识别拒答")
        expect(core.refused("RAG 是检索增强生成") is False, "正常答案不应拒答")

    def test_keyword():
        groups = [["检索"], ["生成", "回答"], "框架"]
        expect(core.missing_keyword("检索增强生成框架", groups) is None, "应全部覆盖")
        expect(core.missing_keyword("检索增强生成", groups) == "框架", "应报缺框架")
        expect(core.missing_keyword("回答", [["生成", "回答"]]) is None, "组内任一即可")
        try:
            core.missing_keyword("x", [[]])
        except ValueError:
            return
        raise AssertionError("空关键词组应抛 ValueError")

    def test_merge():
        base = [{"id": "a", "v": 1}, {"id": "b", "v": 2}]
        extra = [{"id": "b", "v": 20}, {"id": "c", "v": 3}]
        rows = core.merge_cases(base, extra)
        expect([r["id"] for r in rows] == ["a", "b", "c"], f"顺序不对：{rows}")
        expect(rows[1]["v"] == 20, "extra 应覆盖同 id")

    def test_summary():
        results = [
            {"status": "passed"}, {"status": "passed"}, {"status": "failed"}, {"status": "skipped"},
        ]
        summary = core.summarize(results)
        expect(summary == {"total": 4, "passed": 2, "failed": 1, "skipped": 1}, f"汇总不对：{summary}")
        expect(core.summarize([]) == {"total": 0, "passed": 0, "failed": 0, "skipped": 0}, "空汇总不对")

    gate.check("01 归一化", test_norm)
    gate.check("02 拒答判断", test_refused)
    gate.check("03 关键词组", test_keyword)
    gate.check("04 用例合并", test_merge)
    gate.check("05 结果汇总", test_summary)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
