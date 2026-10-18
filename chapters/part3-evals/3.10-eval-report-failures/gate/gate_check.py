"""L3.6 扩展 · 失败诊断 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l310", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l310"] = module
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
            "gate": "L3.6-failure-diagnosis",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


FAILURES = [
    {"case_id": "ok", "type": "rag_fact", "passed": True, "keyword_score": 1, "citation_score": 1, "refusal_ok": 1},
    {"case_id": "offline", "type": "rag_fact", "passed": False, "keyword_score": 0, "citation_score": 1, "refusal_ok": 1},
    {"case_id": "live", "type": "rag_fact", "passed": False, "keyword_score": 0, "citation_score": 0, "refusal_ok": 1, "retrieval_context": "真实上下文"},
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def write(tmp: str, data) -> Path:
        path = Path(tmp) / "failures.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def test_load_live():
        with tempfile.TemporaryDirectory() as tmp:
            failures, mode = core.load_failures(write(tmp, FAILURES))
            expect(len(failures) == 2, f"应只保留失败 case：{failures}")
            expect(mode == "live", f"应推断 live：{mode}")

    def test_load_offline():
        with tempfile.TemporaryDirectory() as tmp:
            failures, mode = core.load_failures(write(tmp, FAILURES[:2]))
            expect(len(failures) == 1 and mode == "offline", f"offline 推断不对：{failures}, {mode}")

    def test_load_errors():
        with tempfile.TemporaryDirectory() as tmp:
            try:
                core.load_failures(Path(tmp) / "missing.json")
            except ValueError:
                pass
            else:
                raise AssertionError("缺文件应抛 ValueError")
            bad = Path(tmp) / "bad.json"
            bad.write_text("{bad", encoding="utf-8")
            try:
                core.load_failures(bad)
            except ValueError:
                return
        raise AssertionError("坏 JSON 应抛 ValueError")

    def test_classify_order():
        expect(core.classify_by_hard_metrics({"refusal_ok": False})[0] == "拒答逻辑层(疑似)", "拒答应优先")
        expect(core.classify_by_hard_metrics({"refusal_ok": True, "citation_score": 0.2, "keyword_score": 0})[0] == "检索/引用层(疑似)", "引用应优先于关键词")
        expect(core.classify_by_hard_metrics({"refusal_ok": True, "citation_score": 1, "keyword_score": 0.2})[0] == "生成层(疑似)", "关键词低应归生成")
        expect(core.classify_by_hard_metrics({"refusal_ok": True, "citation_score": 1, "keyword_score": 1})[0] == "其他/未覆盖(疑似)", "全通过硬指标应归其他")

    def test_summary():
        results = [
            {"layer_suspected": "生成层(疑似)"},
            {"layer_suspected": "生成层(疑似)"},
            {"layer_suspected": "检索/引用层(疑似)"},
        ]
        expect(core.summarize_layers(results) == {"生成层(疑似)": 2, "检索/引用层(疑似)": 1}, "统计不对")
        expect(core.summarize_layers([]) == {}, "空结果应为 {}")

    gate.check("01 加载 live 失败库", test_load_live)
    gate.check("02 加载 offline 失败库", test_load_offline)
    gate.check("03 缺文件/坏 JSON", test_load_errors)
    gate.check("04 分组顺序", test_classify_order)
    gate.check("05 分层统计", test_summary)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
