"""L2.1 文档加载与切分 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l21", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l21"] = module
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
            "gate": "L2.1-load-split",
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

    def test_load_utf8():
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.txt"
            path.write_text("退款3个工作日到账。\n付款后48小时发货。", encoding="utf-8")
            doc = core.load_text(path)
            expect(doc["text"].startswith("退款"), f"正文不对：{doc['text'][:20]}")
            expect(doc["source"] == "doc.txt", f"source 应只取文件名：{doc['source']}")

    def test_load_missing():
        try:
            core.load_text(HERE / "missing-file.txt")
        except ValueError:
            return
        raise AssertionError("不存在文件应抛 ValueError")

    def test_split_empty():
        expect(core.split_text({"text": "   ", "source": "x.txt"}) == [], "空文本应返回 []")
        expect(core.split_text({"text": "", "source": "x.txt"}) == [], "空字符串应返回 []")

    def test_split_basic():
        doc = {"text": "0123456789ABCDEFGHIJ", "source": "doc.txt"}
        rows = core.split_text(doc, chunk_size=10, overlap=2)
        expect(len(rows) == 3, f"应切成 3 段：{len(rows)}")
        expect(all(0 < len(row["text"]) <= 10 for row in rows), "片段长度越界")
        expect([row["index"] for row in rows] == [1, 2, 3], "index 应连续")
        expect(all(row["source"] == "doc.txt" for row in rows), "source 未复制")
        expect(rows[1]["text"][:2] == rows[0]["text"][-2:], "相邻片段没有重叠")

    def test_split_rejects_bad_params():
        doc = {"text": "abcdefghij", "source": "x"}
        for kwargs in ({"chunk_size": 0}, {"overlap": -1}, {"chunk_size": 10, "overlap": 10}):
            try:
                core.split_text(doc, **kwargs)
            except ValueError:
                continue
            raise AssertionError(f"非法参数应抛 ValueError：{kwargs}")

    def test_split_rejects_bad_doc():
        for doc in ({}, {"text": "x"}, {"text": 1, "source": "x"}):
            try:
                core.split_text(doc)  # type: ignore[arg-type]
            except ValueError:
                continue
            raise AssertionError(f"非法文档应抛 ValueError：{doc}")

    gate.check("01 UTF-8 加载与 source", test_load_utf8)
    gate.check("02 拒绝不存在的文件", test_load_missing)
    gate.check("03 空文本返回空", test_split_empty)
    gate.check("04 切分/编号/重叠", test_split_basic)
    gate.check("05 拒绝非法切分参数", test_split_rejects_bad_params)
    gate.check("06 拒绝非法文档", test_split_rejects_bad_doc)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
