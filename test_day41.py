"""
test_day41.py · HTTP 服务接口回归测试
==========================================================
这套测试的关键设计：【完全不调真 LLM，也不建真向量库】。
把 RAG 换成一个假函数注入进去，整条 HTTP 链路照样跑。

为什么必须这么做（面试可以直接讲）：
- 快：全套 1 秒内跑完，能进 pre-commit 和 CI，不然没人会跑
- 稳：不依赖网络和 API key，不会因为上游抖动而红
- 准：测的是【接口契约和工程逻辑】——落库对不对、失败降级对不对、
      trace_id 通不通。模型答得好不好是评测集的事（Day18-26），
      两件事必须分开测，混在一起就是两边都测不明白。

运行：pytest test_day41.py -v
==========================================================
"""

import sys
import types

import pytest

# ---- 在 import day41 之前，先用假模块顶掉重依赖 ----
# day41 的 lifespan 里会 import day12（会加载 FAISS、embedding 模型，几十秒）。
# 测试不需要真检索，注入一个假的：既跑得快，又保证测试不受模型环境影响。
_fake_day12 = types.ModuleType("day12_rag_pdf_sources")
_fake_day12.build_retriever = lambda path: None
sys.modules.setdefault("day12_rag_pdf_sources", _fake_day12)

from fastapi.testclient import TestClient       # noqa: E402

import day41_serve_fastapi as api               # noqa: E402
import day44_sqlite_persistence as store        # noqa: E402


class FakeDoc:
    def __init__(self, source, page=None, text="内容"):
        self.metadata = {"source": source}
        if page is not None:
            self.metadata["page"] = page
        self.page_content = text


def make_answer_fn(answer="检索增强生成", sources=None, raises=None,
                   prompt_tokens=120, completion_tokens=40):
    def fn(question: str) -> dict:
        if raises:
            raise raises
        return {
            "answer": answer,
            "sources": sources if sources is not None else ["handbook.pdf#p3"],
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
    return fn


@pytest.fixture
def client(tmp_path, monkeypatch):
    """每个用例一个独立库 + 一个可控的假 RAG。"""
    monkeypatch.setattr(store, "DB_PATH", str(tmp_path / "api.db"))
    with TestClient(api.app) as c:              # with 才会触发 lifespan
        api.STATE["answer_fn"] = make_answer_fn()
        api.STATE["error"] = None
        yield c
    store.close_conn()


# ============================================================
# 1. 探针：liveness 与 readiness 必须分开
# ============================================================
def test_health_always_ok(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_503_when_not_loaded(client):
    api.STATE["answer_fn"] = None
    api.STATE["error"] = "文件不存在"
    r = client.get("/ready")
    assert r.status_code == 503                  # 没就绪 → 不给流量
    assert client.get("/health").status_code == 200   # 但仍然活着 → 不重启


# ============================================================
# 2. /chat 主链路：答案 + 落库 + trace_id
# ============================================================
def test_chat_returns_answer_and_sources(client):
    r = client.post("/chat", json={"question": "RAG 是什么", "user_id": "u1"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "检索增强生成"
    assert body["sources"] == ["handbook.pdf#p3"]
    assert body["conversation_id"] > 0
    assert r.headers["X-Trace-Id"] == body["trace_id"]   # 响应头与响应体一致


def test_chat_persists_full_observability_fields(client):
    client.post("/chat", json={"question": "RAG 是什么", "user_id": "u1"})
    row = store.get_history("u1")[0]

    assert row["status"] == "ok"
    assert row["prompt_tokens"] == 120 and row["completion_tokens"] == 40
    assert row["cost_usd"] > 0                    # 成本算出来了
    assert row["latency_ms"] >= 0
    assert row["sources"] == ["handbook.pdf#p3"]
    assert row["trace_id"]                        # 能跟日志对上号


def test_trace_id_from_header_is_honored(client):
    """网关传下来的 trace_id 要沿用，不能自己另生成一个——否则全链路断了。"""
    tid = "trace-from-gateway-123"
    r = client.post("/chat", json={"question": "q", "user_id": "u1"},
                    headers={"X-Trace-Id": tid})
    assert r.json()["trace_id"] == tid
    assert store.get_history("u1")[0]["trace_id"] == tid


def test_chat_503_when_not_ready(client):
    api.STATE["answer_fn"] = None
    assert client.post("/chat", json={"question": "q"}).status_code == 503


# ============================================================
# 3. 失败路径：降级 + 失败也要落库
# ============================================================
def test_chat_failure_returns_502_without_stacktrace(client):
    api.STATE["answer_fn"] = make_answer_fn(raises=TimeoutError("上游超时"))
    r = client.post("/chat", json={"question": "q", "user_id": "u1"})

    assert r.status_code == 502
    assert "上游超时" not in r.text      # 内部错误细节不能泄漏给用户
    assert "Traceback" not in r.text


def test_failed_request_is_still_logged(client):
    """只记成功的话失败率永远是 0% —— 等于没有监控。这条用例钉死它。"""
    api.STATE["answer_fn"] = make_answer_fn(raises=TimeoutError("上游超时"))
    client.post("/chat", json={"question": "会失败的问题", "user_id": "u1"})

    row = store.get_history("u1")[0]
    assert row["status"] == "error"
    assert "TimeoutError" in row["error"]
    assert row["question"] == "会失败的问题"


# ============================================================
# 4. 输入校验：第一道成本与安全防线
# ============================================================
@pytest.mark.parametrize("payload", [
    {"question": ""},                    # 空问题
    {"question": "x" * 1001},            # 超长 prompt（打爆成本）
    {"user_id": "u1"},                   # 缺 question
    {"question": "q", "user_id": "x" * 100},
])
def test_invalid_input_rejected_with_422(client, payload):
    assert client.post("/chat", json=payload).status_code == 422


def test_injection_payload_is_stored_not_executed(client):
    """注入串走完整条 HTTP → 数据层链路，必须原样落库、表还在。"""
    payload = "'); DROP TABLE conversations; --"
    r = client.post("/chat", json={"question": payload, "user_id": "u1"})
    assert r.status_code == 200
    assert store.get_history("u1")[0]["question"] == payload


# ============================================================
# 5. /feedback：数据飞轮入口
# ============================================================
def test_feedback_roundtrip(client):
    cid = client.post("/chat", json={"question": "q", "user_id": "u1"}).json()["conversation_id"]
    assert client.post("/feedback", json={"conversation_id": cid, "rating": -1,
                                          "comment": "答非所问"}).status_code == 200

    cases = []
    import json as _json
    from pathlib import Path
    out = store.export_eval_set(out_path=str(Path(store.DB_PATH).parent / "e.json"))
    cases = _json.loads(Path(out).read_text(encoding="utf-8"))
    assert [c["question"] for c in cases] == ["q"]      # 点踩的问题进了评测集


def test_feedback_invalid_rating_422(client):
    cid = client.post("/chat", json={"question": "q", "user_id": "u1"}).json()["conversation_id"]
    assert client.post("/feedback", json={"conversation_id": cid, "rating": 99}).status_code == 422


def test_feedback_unknown_conversation_404(client):
    r = client.post("/feedback", json={"conversation_id": 99999, "rating": 1})
    assert r.status_code == 404


# ============================================================
# 6. /stats 与 /history
# ============================================================
def test_stats_reflects_success_and_failure(client):
    client.post("/chat", json={"question": "ok1", "user_id": "u1"})
    api.STATE["answer_fn"] = make_answer_fn(raises=RuntimeError("boom"))
    client.post("/chat", json={"question": "bad", "user_id": "u1"})

    rows = client.get("/stats?days=1").json()["rows"]
    assert rows[0]["n"] == 2
    assert rows[0]["error_rate_pct"] == pytest.approx(50.0)
    assert rows[0]["cost_usd"] > 0


def test_history_pagination_and_isolation(client):
    for i in range(5):
        client.post("/chat", json={"question": f"q{i}", "user_id": "u1"})
    client.post("/chat", json={"question": "别人的", "user_id": "u2"})

    page1 = client.get("/history?user_id=u1&limit=3").json()["items"]
    assert len(page1) == 3
    page2 = client.get(f"/history?user_id=u1&limit=3&before_id={page1[-1]['id']}").json()["items"]
    assert len(page2) == 2
    assert {r["question"] for r in page1 + page2} == {f"q{i}" for i in range(5)}   # 不串用户


# ============================================================
# 7. build_answer_fn 单元测试：一次检索、来源、token 都要对
# ============================================================
def test_build_answer_fn_single_retrieval_and_usage():
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    calls = []

    class R:
        def invoke(self, q):
            calls.append(q)
            return [FakeDoc("a.pdf", page=3), FakeDoc("b.md")]

    fake_llm = RunnableLambda(lambda _: AIMessage(
        content="答案", usage_metadata={"input_tokens": 11, "output_tokens": 7,
                                        "total_tokens": 18}))

    out = api.build_answer_fn(R(), fake_llm)("问题")
    assert len(calls) == 1                       # 只检索一次，不为了拿来源再查一遍
    assert out["sources"] == ["a.pdf#p3", "b.md"]
    assert (out["prompt_tokens"], out["completion_tokens"]) == (11, 7)


def test_estimate_cost_is_positive_and_ordered():
    assert api.estimate_cost(0, 0) == 0
    # 输出 token 比输入贵，成本函数必须体现这一点
    assert api.estimate_cost(0, 1000) > api.estimate_cost(1000, 0)
