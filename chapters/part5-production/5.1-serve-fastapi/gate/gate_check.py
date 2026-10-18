"""L5.1 FastAPI 服务与可靠性 · 离线 gate 验收。

用法（仓库根目录）：
    python chapters/part5-production/5.1-serve-fastapi/gate/gate_check.py
    python chapters/part5-production/5.1-serve-fastapi/gate/gate_check.py --module 你的实现.py

默认检查同目录 starter.py。全部 PASS 时退出码为 0，并写出 gate_report.json。
不调用真实模型、不连数据库；answer_fn 和 store 都由脚本注入。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    sys.path.insert(0, str(CHAPTER))
    spec = importlib.util.spec_from_file_location("candidate_l51", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l51"] = module
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
            "gate": "L5.1-fastapi-reliability",
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


class FakeStore:
    def __init__(self) -> None:
        self.qa: list[dict] = []
        self.feedback: list[dict] = []
        self.stats_calls: list[int] = []
        self.history_calls: list[dict] = []

    def save_qa(self, **kwargs) -> int:
        self.qa.append(kwargs)
        return len(self.qa)

    def save_feedback(self, conversation_id: int, rating: int, comment: str | None = None) -> int:
        if conversation_id < 1:
            raise ValueError("对话不存在")
        self.feedback.append(
            {"conversation_id": conversation_id, "rating": rating, "comment": comment}
        )
        return len(self.feedback)

    def daily_stats(self, days: int) -> list[dict]:
        self.stats_calls.append(days)
        return [{"day": "2026-10-18", "requests": 1, "cost_usd": 0.001}]

    def get_history(self, user_id: str, limit: int = 20, before_id: int | None = None) -> list[dict]:
        self.history_calls.append({"user_id": user_id, "limit": limit, "before_id": before_id})
        return [{"id": 1, "question": "退款多久"}]


def ok_answer(question: str) -> dict:
    return {
        "answer": f"回答：{question}",
        "sources": ["refund.md#1"],
        "prompt_tokens": 10,
        "completion_tokens": 5,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def client(app):
        return TestClient(app, raise_server_exceptions=False)

    def test_cost_estimate():
        zero = core.estimate_cost(0, 0)
        prompt_only = core.estimate_cost(1_000_000, 0)
        completion_only = core.estimate_cost(0, 1_000_000)
        both = core.estimate_cost(1_000_000, 1_000_000)
        expect(zero == 0, f"0 token 成本应为 0：{zero}")
        expect(prompt_only > 0 and completion_only > 0, "输入/输出成本应大于 0")
        expect(both > prompt_only and both > completion_only, "总成本应大于单项")
        expect(core.estimate_cost(-100, -100) == 0, "负 token 应按 0 处理")

    def test_retry_success_first_try():
        calls = []

        def fn():
            calls.append(1)
            return "ok"

        expect(core.call_with_retry(fn, attempts=2) == "ok", "应返回结果")
        expect(len(calls) == 1, "成功时不应重试")

    def test_retry_timeout_then_success():
        calls = []

        def fn():
            calls.append(1)
            if len(calls) == 1:
                raise TimeoutError("timeout")
            return "ok"

        expect(core.call_with_retry(fn, attempts=2) == "ok", "第二次成功应返回")
        expect(len(calls) == 2, "应重试一次")

    def test_no_retry_on_value_error():
        calls = []

        def fn():
            calls.append(1)
            raise ValueError("bad input")

        try:
            core.call_with_retry(fn, attempts=3)
        except ValueError:
            expect(len(calls) == 1, "非瞬时错误不应重试")
            return
        raise AssertionError("ValueError 应原样抛出")

    def test_retry_exhausted():
        calls = []

        def fn():
            calls.append(1)
            raise TimeoutError("timeout")

        try:
            core.call_with_retry(fn, attempts=2)
        except core.UpstreamError:
            expect(len(calls) == 2, "重试次数不对")
            return
        raise AssertionError("重试耗尽应抛 UpstreamError")

    def test_retry_rejects_zero_attempts():
        try:
            core.call_with_retry(lambda: "x", attempts=0)
        except ValueError:
            return
        raise AssertionError("attempts=0 应抛 ValueError")

    def test_retry_enforces_timeout():
        def slow():
            time.sleep(0.2)
            return "late"

        try:
            core.call_with_retry(slow, attempts=1, timeout_s=0.05)
        except core.UpstreamError:
            return
        raise AssertionError("超时应抛 UpstreamError")

    def test_health_and_not_ready_without_answer():
        app = core.create_app(answer_fn=None, store=FakeStore())
        with client(app) as c:
            expect(c.get("/health").status_code == 200, "/health 应永远 200")
            expect(c.get("/ready").status_code == 503, "无 answer_fn 时 /ready 应 503")
            expect(c.post("/chat", json={"question": "你好"}).status_code == 503, "无 answer_fn 时 /chat 应 503")

    def test_ready_with_answer():
        app = core.create_app(answer_fn=ok_answer, store=FakeStore())
        with client(app) as c:
            expect(c.get("/health").status_code == 200, "/health 应 200")
            expect(c.get("/ready").status_code == 200, "/ready 应 200")

    def test_chat_success_and_store():
        store = FakeStore()
        app = core.create_app(answer_fn=ok_answer, store=store)
        with client(app) as c:
            resp = c.post("/chat", json={"question": "退款多久", "user_id": "u1"})
            expect(resp.status_code == 200, f"/chat 应 200：{resp.status_code} {resp.text}")
            body = resp.json()
            for key in ("answer", "sources", "conversation_id", "trace_id", "latency_ms"):
                expect(key in body, f"响应缺字段：{key}")
            expect(body["sources"] == ["refund.md#1"], f"sources 不对：{body['sources']}")
            expect(resp.headers.get("X-Trace-Id") == body["trace_id"], "响应头与 body 的 trace_id 应一致")
            expect(len(store.qa) == 1, "成功请求应落库一次")
            saved = store.qa[0]
            expect(saved.get("question") == "退款多久", f"落库问题不对：{saved}")
            expect(saved.get("status") in (None, "ok", "success"), f"成功请求状态不对：{saved}")
            expect(saved.get("sources") == ["refund.md#1"], f"落库来源不对：{saved}")

    def test_chat_echoes_incoming_trace_id():
        app = core.create_app(answer_fn=ok_answer, store=FakeStore())
        with client(app) as c:
            resp = c.post("/chat", json={"question": "你好"}, headers={"X-Trace-Id": "trace-abc"})
            expect(resp.status_code == 200, "请求应成功")
            expect(resp.headers.get("X-Trace-Id") == "trace-abc", "应沿用调用方 trace_id")
            expect(resp.json()["trace_id"] == "trace-abc", "body 应沿用调用方 trace_id")

    def test_chat_validates_question_length():
        app = core.create_app(answer_fn=ok_answer, store=FakeStore())
        with client(app) as c:
            expect(c.post("/chat", json={"question": ""}).status_code == 422, "空问题应 422")
            expect(c.post("/chat", json={"question": "x" * 1001}).status_code == 422, "超长问题应 422")

    def test_chat_timeout_maps_to_502_and_logs_error():
        store = FakeStore()

        def timeout(_question: str) -> dict:
            raise TimeoutError("upstream timeout")

        app = core.create_app(answer_fn=timeout, store=store)
        with client(app) as c:
            resp = c.post("/chat", json={"question": "退款多久"})
            expect(resp.status_code == 502, f"上游超时应 502：{resp.status_code} {resp.text}")
            expect(resp.headers.get("X-Trace-Id"), "错误响应也应有 trace_id")
            expect("trace_id" in resp.json(), "错误 body 应含 trace_id")
            expect(len(store.qa) == 1, "失败请求也要落库")
            expect(store.qa[0].get("status") == "error", f"失败请求状态应为 error：{store.qa[0]}")

    def test_chat_empty_answer_maps_to_502():
        store = FakeStore()

        def empty(_question: str) -> dict:
            return {"answer": "", "sources": [], "prompt_tokens": 1, "completion_tokens": 0}

        app = core.create_app(answer_fn=empty, store=store)
        with client(app) as c:
            resp = c.post("/chat", json={"question": "退款多久"})
            expect(resp.status_code == 502, f"空答案应 502：{resp.status_code}")
            expect(store.qa and store.qa[0].get("status") == "error", "空答案应记录为失败")

    def test_chat_unhandled_exception_is_500_without_stack():
        store = FakeStore()

        def boom(_question: str) -> dict:
            raise RuntimeError("boom-secret")

        app = core.create_app(answer_fn=boom, store=store)
        with client(app) as c:
            resp = c.post("/chat", json={"question": "退款多久"})
            expect(resp.status_code == 500, f"未处理异常应 500：{resp.status_code} {resp.text}")
            expect("trace_id" in resp.json(), "500 body 应含 trace_id")
            expect("Traceback" not in resp.text and "boom-secret" not in resp.text, "不应泄露堆栈/内部信息")

    def test_feedback_and_read_endpoints():
        store = FakeStore()
        app = core.create_app(answer_fn=ok_answer, store=store)
        with client(app) as c:
            chat = c.post("/chat", json={"question": "退款多久"})
            conversation_id = chat.json()["conversation_id"]
            expect(c.post("/feedback", json={"conversation_id": conversation_id, "rating": 1}).status_code == 200, "反馈应成功")
            expect(len(store.feedback) == 1, "反馈应落库")
            expect(c.post("/feedback", json={"conversation_id": conversation_id, "rating": 0}).status_code == 422, "非法 rating 应 422")
            stats = c.get("/stats?days=3")
            expect(stats.status_code == 200 and "rows" in stats.json(), "stats 应返回 rows")
            expect(store.stats_calls == [3], f"stats 应把 days 传给 store：{store.stats_calls}")
            history = c.get("/history?user_id=u1&limit=5")
            expect(history.status_code == 200 and "items" in history.json(), "history 应返回 items")
            expect(store.history_calls and store.history_calls[0]["user_id"] == "u1", "history 应传 user_id")

    def test_chat_retries_transient_failure():
        calls = []

        def flaky(question: str) -> dict:
            calls.append(question)
            if len(calls) == 1:
                raise TimeoutError("first timeout")
            return ok_answer(question)

        app = core.create_app(answer_fn=flaky, store=FakeStore())
        with client(app) as c:
            resp = c.post("/chat", json={"question": "退款多久"})
            expect(resp.status_code == 200, f"瞬时失败应重试成功：{resp.status_code} {resp.text}")
            expect(len(calls) == 2, f"应调用两次：{len(calls)}")

    gate.check("01 成本估算", test_cost_estimate)
    gate.check("02 首次成功不重试", test_retry_success_first_try)
    gate.check("03 超时后重试成功", test_retry_timeout_then_success)
    gate.check("04 非瞬时错误不重试", test_no_retry_on_value_error)
    gate.check("05 重试耗尽抛 UpstreamError", test_retry_exhausted)
    gate.check("06 拒绝 attempts=0", test_retry_rejects_zero_attempts)
    gate.check("07 超时上限生效", test_retry_enforces_timeout)
    gate.check("08 无 answer_fn 时健康/就绪/聊天", test_health_and_not_ready_without_answer)
    gate.check("09 有 answer_fn 时就绪", test_ready_with_answer)
    gate.check("10 聊天成功并落库", test_chat_success_and_store)
    gate.check("11 透传调用方 trace_id", test_chat_echoes_incoming_trace_id)
    gate.check("12 校验问题长度", test_chat_validates_question_length)
    gate.check("13 超时映射 502 并记录失败", test_chat_timeout_maps_to_502_and_logs_error)
    gate.check("14 空答案映射 502", test_chat_empty_answer_maps_to_502)
    gate.check("15 未处理异常 500 且不泄堆栈", test_chat_unhandled_exception_is_500_without_stack)
    gate.check("16 反馈/stats/history", test_feedback_and_read_endpoints)
    gate.check("17 服务层重试瞬时失败", test_chat_retries_transient_failure)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
