"""L2.3 最小 RAG · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l23", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l23"] = module
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
            "gate": "L2.3-minimal-rag",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


class Chat:
    def __init__(self, reply: str | Exception):
        self.reply = reply
        self.calls: list[list[dict]] = []

    def __call__(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    docs = [
        {"text": "aaa", "source": "a"},
        {"text": "bbb", "source": "b"},
    ]

    def test_format_context():
        text = core.format_context(docs)
        expect(text == "[a]\naaa\n\n[b]\nbbb", f"上下文格式不对：{text!r}")
        expect(core.format_context([]) == "", "空列表应返回空串")

    def test_format_rejects_bad():
        for args in (([{"text": "x", "source": "a"}], -1), ([{"text": 1, "source": "a"}], None), ([{}], None)):
            try:
                core.format_context(*args)
            except ValueError:
                continue
            raise AssertionError(f"非法输入应抛 ValueError：{args}")

    def test_answer_with_evidence():
        chat = Chat("退款3个工作日到账")
        result = core.answer_with_rag("退款多久", lambda q: list(docs), chat)
        expect(result["answer"] == "退款3个工作日到账", f"答案不对：{result}")
        expect(result["sources"] == ["a", "b"], f"sources 不对：{result['sources']}")
        expect(result["refused"] is False and result["error"] is None, f"状态不对：{result}")
        expect(chat.calls and "aaa" in chat.calls[0][1]["content"], "上下文没有进入消息")

    def test_answer_without_evidence():
        chat = Chat("不应调用")
        result = core.answer_with_rag("量子纠缠", lambda q: [], chat)
        expect(result["refused"] is True and result["sources"] == [], f"应拒答：{result}")
        expect(chat.calls == [], "无证据不应调用模型")

    def test_answer_empty_question():
        try:
            core.answer_with_rag("  ", lambda q: [], Chat("x"))
        except ValueError:
            return
        raise AssertionError("空问题应抛 ValueError")

    def test_answer_retrieval_error():
        def broken(_q):
            raise RuntimeError("index down")

        result = core.answer_with_rag("x", broken, Chat("x"))
        expect(result["refused"] is True and result["error"] == "retrieval_error", f"检索异常处理不对：{result}")

    def test_answer_timeout():
        result = core.answer_with_rag("x", lambda q: list(docs), Chat(TimeoutError("timeout")))
        expect(result["refused"] is True and result["error"] == "timeout", f"超时处理不对：{result}")

    def test_answer_empty_response():
        result = core.answer_with_rag("x", lambda q: list(docs), Chat("   "))
        expect(result["refused"] is True and result["error"] == "empty_response", f"空回答处理不对：{result}")

    def test_answer_context_budget():
        chat = Chat("ok")
        result = core.answer_with_rag("x", lambda q: list(docs), chat, max_context_chars=8)
        expect(result["sources"] == ["a"], f"预算只应容纳第一段：{result['sources']}")
        expect("bbb" not in chat.calls[0][1]["content"], "超预算片段不应进入上下文")

    def test_answer_sources_dedupe():
        rows = [{"text": "a1", "source": "a"}, {"text": "a2", "source": "a"}]
        result = core.answer_with_rag("x", lambda q: rows, Chat("ok"))
        expect(result["sources"] == ["a"], f"来源应去重：{result['sources']}")

    gate.check("01 上下文格式", test_format_context)
    gate.check("02 拒绝非法上下文", test_format_rejects_bad)
    gate.check("03 有证据回答并引用", test_answer_with_evidence)
    gate.check("04 无证据拒答", test_answer_without_evidence)
    gate.check("05 空问题拒绝", test_answer_empty_question)
    gate.check("06 检索异常降级", test_answer_retrieval_error)
    gate.check("07 模型超时降级", test_answer_timeout)
    gate.check("08 空回答降级", test_answer_empty_response)
    gate.check("09 上下文预算", test_answer_context_budget)
    gate.check("10 来源去重", test_answer_sources_dedupe)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
