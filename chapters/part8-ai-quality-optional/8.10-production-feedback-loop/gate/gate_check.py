"""L3.2 扩展 · 反馈闭环 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l810", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l810"] = module
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
            "gate": "L3.2-feedback-loop",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def item(case_id="c1", rating=-1, status="pending") -> dict:
    return {"case_id": case_id, "question": "q", "answer": "a", "rating": rating, "reason": "bad", "sources": ["s1"], "status": status}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_submit():
        queue = core.FeedbackQueue()
        expect(queue.submit(item()) is True, "首次应入队")
        expect(queue.submit(item()) is False, "重复应返回 False")

    def test_validation():
        for bad in (item(rating=0), item(case_id=" ")):
            try:
                core.FeedbackQueue().submit(bad)
            except ValueError:
                continue
            raise AssertionError(f"非法项应报错：{bad}")

    def test_review():
        queue = core.FeedbackQueue()
        queue.submit(item("pos", rating=1))
        queue.submit(item("neg", rating=-1))
        queue.submit(item("done", rating=-1, status="approved"))
        expect([row["case_id"] for row in queue.review_queue()] == ["neg"], f"审核队列不对：{queue.review_queue()}")

    def test_approve_export():
        queue = core.FeedbackQueue()
        queue.submit(item("neg"))
        approved = queue.approve("neg")
        expect(approved["status"] == "approved", "应标记 approved")
        try:
            queue.approve("missing")
        except KeyError:
            pass
        else:
            raise AssertionError("不存在应 KeyError")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            expect(queue.export_regression_cases(path) == 1, "导出数量不对")
            rows = json.loads(path.read_text(encoding="utf-8"))
            expect(rows[0]["id"] == "neg" and rows[0]["answer"] == "a", f"导出内容不对：{rows}")

    def test_export_only_approved():
        queue = core.FeedbackQueue()
        queue.submit(item("pending"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            expect(queue.export_regression_cases(path) == 0, "未审核不应导出")

    gate.check("01 入队/去重", test_submit)
    gate.check("02 字段校验", test_validation)
    gate.check("03 审核队列", test_review)
    gate.check("04 审核/导出", test_approve_export)
    gate.check("05 只导出 approved", test_export_only_approved)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
