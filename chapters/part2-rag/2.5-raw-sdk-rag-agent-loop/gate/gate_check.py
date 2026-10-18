"""L1.6 手写 Harness · 离线 gate 验收。

用法（仓库根目录）：
    python chapters/part2-rag/2.5-raw-sdk-rag-agent-loop/gate/gate_check.py
    python chapters/part2-rag/2.5-raw-sdk-rag-agent-loop/gate/gate_check.py --module 你的实现.py

默认检查同目录 starter.py。全部 PASS 时退出码为 0，并写出 gate_report.json。
不调用真实模型；所有模型行为由脚本化 chat_fn 注入。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    sys.path.insert(0, str(CHAPTER))
    spec = importlib.util.spec_from_file_location("candidate_l16", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l16"] = module
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
        except Exception as exc:  # noqa: BLE001 - gate 要报告所有失败
            self.rows.append(
                {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
            )
        else:
            self.rows.append({"name": name, "ok": True, "error": ""})

    def report(self, module_path: Path) -> int:
        passed = sum(row["ok"] for row in self.rows)
        total = len(self.rows)
        for row in self.rows:
            mark = "PASS" if row["ok"] else "FAIL"
            suffix = "" if row["ok"] else f"  <- {row['error']}"
            print(f"[{mark}] {row['name']}{suffix}")
        print(f"\n{passed}/{total} passed")
        if passed != total:
            print("gate 未通过：先修 FAIL 项，不要打开参考实现。")
        out = {
            "gate": "L1.6-harness",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return 0 if passed == total else 1


class ScriptedChat:
    """按顺序返回预设回复；记录每次 messages，便于检查调用行为。"""

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls: list[list[dict]] = []

    def __call__(self, messages: list[dict]) -> str:
        self.calls.append(list(messages))
        if not self.replies:
            raise AssertionError("chat_fn 被调用的次数超过脚本预设")
        return self.replies.pop(0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def chunks():
        return [
            core.Chunk("退款审核通过后3个工作日到账。", "refund.md", 1),
            core.Chunk("付款后48小时内发货。", "shipping.md", 1),
            core.Chunk("退款超过7天请联系人工。", "refund.md", 2),
        ]

    def test_split_empty():
        expect(core.split_text("   ", "doc.md") == [], "空文本应返回 []")

    def test_split_basic():
        rows = core.split_text("abcdefghijklm", "doc.md", chunk_size=10, overlap=0)
        expect(len(rows) == 2, f"10/0 切分应得到 2 段，实际 {len(rows)}")
        expect(rows[0].text == "abcdefghij", "第一段内容不对")
        expect(rows[1].text == "klm", "第二段内容不对")
        expect([r.index for r in rows] == [1, 2], "index 应从 1 连续编号")
        expect(all(r.source == "doc.md" for r in rows), "source 应原样保留")

    def test_split_overlap_and_limits():
        rows = core.split_text("0123456789ABCDEFGHIJ", "doc.md", chunk_size=10, overlap=3)
        expect(all(len(r.text) <= 10 for r in rows), "片段长度超过 chunk_size")
        expect(all(r.text.strip() for r in rows), "不应产生空片段")
        expect(len(rows) >= 2, "带 overlap 时应覆盖全部文本")

    def test_split_rejects_bad_params():
        for kwargs in ({"chunk_size": 0}, {"overlap": -1}, {"chunk_size": 10, "overlap": 10}):
            try:
                core.split_text("abcdefghij", "doc.md", **kwargs)
            except ValueError:
                continue
            raise AssertionError(f"非法参数应抛 ValueError：{kwargs}")

    def test_retrieve_ranks_and_filters():
        rows = core.retrieve("退款多久", chunks(), k=3)
        expect(rows, "相关查询不应返回空")
        expect(rows[0].source == "refund.md", "退款查询应优先命中文档")
        expect(len(rows) <= 3, "k 没有生效")
        expect(core.retrieve("zzzz", chunks()) == [], "无匹配查询应返回 []")
        expect(core.retrieve("   ", chunks()) == [], "空查询应返回 []")
        expect(len(core.retrieve("退款", chunks(), k=1)) == 1, "k=1 没有生效")

    def test_answer_with_evidence():
        chat = ScriptedChat(["退款审核通过后3个工作日到账。"])
        result = core.answer("到账", chunks(), chat)
        expect(result["refused"] is False, "有证据时不应拒答")
        expect(result["sources"] == ["refund.md#1"], f"来源不对：{result['sources']}")
        expect("3个工作日" in result["answer"], "答案没有带回模型输出")
        expect(result["error"] is None, f"成功时 error 应为 None：{result['error']}")
        expect(len(chat.calls) == 1, "应只调用一次模型")

    def test_answer_refuses_without_evidence():
        chat = ScriptedChat(["不应该被调用"])
        result = core.answer("量子纠缠", chunks(), chat)
        expect(result["refused"] is True, "无证据应拒答")
        expect(result["sources"] == [], "拒答不应附来源")
        expect(chat.calls == [], "无证据时不应调用模型")

    def test_answer_rejects_empty_question():
        result = core.answer("   ", chunks(), ScriptedChat(["x"]))
        expect(result["refused"] is True, "空问题应拒答")
        expect(result["sources"] == [], "空问题不应附来源")

    def test_answer_handles_timeout():
        def timeout(_messages):
            raise TimeoutError("upstream timeout")

        result = core.answer("到账", chunks(), timeout)
        expect(result["refused"] is True, "模型超时应拒答而不是崩溃")
        expect("timeout" in str(result["error"]).lower(), f"error 应可读：{result['error']}")

    def test_answer_handles_empty_response():
        result = core.answer("到账", chunks(), ScriptedChat([""]))
        expect(result["refused"] is True, "空回答应视为失败")
        expect("empty" in str(result["error"]).lower(), f"error 应指出空回答：{result['error']}")

    def test_agent_final_after_tool():
        chat = ScriptedChat(["Action: calc[2+2]", "Final: 4"])
        result = core.run_agent("计算 2+2", chat, {"calc": lambda arg: str(eval(arg))})
        expect(result["answer"] == "4", f"最终答案不对：{result['answer']}")
        expect(result["stopped_reason"] == "final", "停止原因应为 final")
        expect(len(result["trace"]) == 1, f"轨迹应有 1 步：{result['trace']}")
        step = result["trace"][0]
        expect(step["ok"] is True, "成功工具调用应标记 ok")
        expect(step["tool"] == "calc" and step["observation"] == "4", f"轨迹内容不对：{step}")

    def test_agent_unknown_tool_is_readable():
        chat = ScriptedChat(["Action: nope[x]", "Final: 无法查询"])
        result = core.run_agent("查一下", chat, {})
        expect(result["stopped_reason"] == "final", "未知工具后仍应允许模型收尾")
        expect(result["trace"][0]["ok"] is False, "未知工具应标记失败")
        expect("unknown" in str(result["trace"][0].get("error", "")).lower(), "错误应可读")
        expect("无法查询" in result["answer"], "最终回答丢失")

    def test_agent_tool_exception_is_readable():
        def boom(_arg):
            raise RuntimeError("tool down")

        chat = ScriptedChat(["Action: boom[x]", "Final: 工具失败了"])
        result = core.run_agent("调用故障工具", chat, {"boom": boom})
        expect(result["trace"][0]["ok"] is False, "工具异常应标记失败")
        expect("tool_error" in str(result["trace"][0].get("error", "")), "错误应标记 tool_error")
        expect(result["stopped_reason"] == "final", "工具失败后仍应允许收尾")

    def test_agent_stops_at_max_steps():
        chat = ScriptedChat(["Action: calc[1+1]"] * 3)
        result = core.run_agent("一直算", chat, {"calc": lambda arg: "2"}, max_steps=3)
        expect(result["stopped_reason"] == "max_steps", "应在上限停止")
        expect(len(result["trace"]) == 3, f"轨迹应为 3 步：{len(result['trace'])}")

    def test_agent_unparsed_output():
        chat = ScriptedChat(["我不知道"])
        result = core.run_agent("随口问", chat, {})
        expect(result["stopped_reason"] == "unparsed", "无法解析时应标记 unparsed")
        expect(result["answer"] == "我不知道", "应保留模型原文")

    def test_agent_model_error():
        def timeout(_messages):
            raise TimeoutError("upstream timeout")

        result = core.run_agent("查订单", timeout, {})
        expect(result["stopped_reason"] == "model_error", "模型异常应标记 model_error")
        expect(result["answer"], "应给出可读的失败提示")

    gate.check("01 空文本切分", test_split_empty)
    gate.check("02 基本切分与编号", test_split_basic)
    gate.check("03 overlap 与长度上限", test_split_overlap_and_limits)
    gate.check("04 拒绝非法切分参数", test_split_rejects_bad_params)
    gate.check("05 检索排序与过滤", test_retrieve_ranks_and_filters)
    gate.check("06 有证据时回答并引用", test_answer_with_evidence)
    gate.check("07 无证据时拒答且不调用模型", test_answer_refuses_without_evidence)
    gate.check("08 空问题拒答", test_answer_rejects_empty_question)
    gate.check("09 模型超时降级", test_answer_handles_timeout)
    gate.check("10 空回答降级", test_answer_handles_empty_response)
    gate.check("11 Agent 调工具后收尾", test_agent_final_after_tool)
    gate.check("12 未知工具可读失败", test_agent_unknown_tool_is_readable)
    gate.check("13 工具异常可读失败", test_agent_tool_exception_is_readable)
    gate.check("14 最大步数终止", test_agent_stops_at_max_steps)
    gate.check("15 无法解析时保留原文", test_agent_unparsed_output)
    gate.check("16 模型异常终止", test_agent_model_error)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
