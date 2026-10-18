"""L3.6 扩展 · Prompt A/B 指标 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l38", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l38"] = module
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
            "gate": "L3.6-prompt-ab",
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

    def test_normalize():
        expect(core.normalize("  RAG  是 什么 ") == "rag是什么", "归一化不对")

    def test_refused():
        expect(core.looks_refused("信息不足，无法回答") is True, "应识别拒答")
        expect(core.looks_refused("RAG 是检索增强生成") is False, "正常答案不应拒答")

    def test_keyword():
        expect(core.keyword_score("检索增强生成", ["检索", "生成"]) == 1.0, "全命中应为 1")
        expect(core.keyword_score("检索", ["检索", "生成"]) == 0.5, "命中一半应为 .5")
        expect(core.keyword_score("x", []) == 1.0, "无关键词应为 1")

    def test_citation():
        expect(core.citation_score("来源：notes", ["notes"]) == 1.0, "来源命中应为 1")
        expect(core.citation_score("无来源", ["notes"]) == 0.0, "未命中应为 0")
        expect(core.citation_score("x", []) == 1.0, "无来源标注应为 1")

    def test_alignment():
        expect(core.refusal_alignment("信息不足", True) == 1.0, "正确拒答应 1")
        expect(core.refusal_alignment("信息不足", False) == 0.0, "误拒答应 0")
        expect(core.refusal_alignment("答案", False) == 1.0, "正常应答应 1")

    gate.check("01 归一化", test_normalize)
    gate.check("02 拒答判断", test_refused)
    gate.check("03 关键词分", test_keyword)
    gate.check("04 引用分", test_citation)
    gate.check("05 拒答一致性", test_alignment)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
