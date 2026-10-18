"""L2.3 扩展 · PDF 与来源溯源 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l26", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l26"] = module
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
            "gate": "L2.3-pdf-sources",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


DOCS = [
    {"text": "退款3个工作日到账。", "source": "manual.pdf", "page": 2},
    {"text": "发货48小时。", "source": "faq.md"},
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_load_pages():
        rows = core.load_pages([(1, "第一页"), (2, "   "), (3, "第三页")], "doc.pdf")
        expect(len(rows) == 2, f"空白页应跳过：{rows}")
        expect(rows[0] == {"text": "第一页", "source": "doc.pdf", "page": 1}, f"第一页不对：{rows[0]}")
        expect(rows[1]["page"] == 3, "页码应保持原值")

    def test_load_rejects_bad():
        for pages, source in (([(0, "x")], "a.pdf"), ([("1", "x")], "a.pdf"), ([(1, "x")], "")):
            try:
                core.load_pages(pages, source)
            except ValueError:
                continue
            raise AssertionError(f"非法页/来源应抛 ValueError：{pages}, {source!r}")

    def test_format():
        text = core.format_context(DOCS)
        expect("[来源：manual.pdf 第2页]" in text, f"缺页码标记：{text}")
        expect("[来源：faq.md]" in text, f"缺无页码标记：{text}")
        expect(text.index("manual.pdf") < text.index("faq.md"), "顺序不对")
        expect(core.format_context([]) == "", "空列表应返回空串")

    def test_format_rejects_bad():
        for docs in ([{"text": "x"}], [{"text": 1, "source": "a"}], [{"text": "x", "source": "a", "page": 0}]):
            try:
                core.format_context(docs)
            except ValueError:
                continue
            raise AssertionError(f"非法 docs 应抛 ValueError：{docs}")

    def test_verify_ok():
        result = core.verify_citations("答案【来源：manual.pdf 第2页】【来源：faq.md】", DOCS)
        expect(result["ok"] is True, f"引用应通过：{result}")
        expect(result["cited"] == ["manual.pdf#p2", "faq.md"], f"cited 不对：{result['cited']}")
        expect(result["unknown"] == [], f"unknown 应为空：{result['unknown']}")

    def test_verify_unknown_page():
        result = core.verify_citations("答案【来源：manual.pdf 第3页】", DOCS)
        expect(result["ok"] is False, "未知页码不应通过")
        expect(result["unknown"] == ["manual.pdf#p3"], f"unknown 不对：{result['unknown']}")

    def test_verify_fabricated_source():
        result = core.verify_citations("答案【来源：fake.pdf】", DOCS)
        expect(result["ok"] is False and result["unknown"] == ["fake.pdf"], f"伪造来源不对：{result}")

    def test_verify_no_citation():
        result = core.verify_citations("答案没有来源", DOCS)
        expect(result["ok"] is False and result["cited"] == [], f"无引用不应通过：{result}")

    def test_verify_rejects_bad():
        for answer, docs in ((1, DOCS), ("x", [{"text": "x"}])):
            try:
                core.verify_citations(answer, docs)  # type: ignore[arg-type]
            except ValueError:
                continue
            raise AssertionError("非法输入应抛 ValueError")

    gate.check("01 按页加载并跳过空白", test_load_pages)
    gate.check("02 拒绝非法页/来源", test_load_rejects_bad)
    gate.check("03 带页码上下文", test_format)
    gate.check("04 拒绝非法片段", test_format_rejects_bad)
    gate.check("05 引用全部命中", test_verify_ok)
    gate.check("06 未知页码", test_verify_unknown_page)
    gate.check("07 伪造来源", test_verify_fabricated_source)
    gate.check("08 无引用", test_verify_no_citation)
    gate.check("09 拒绝非法引用输入", test_verify_rejects_bad)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
