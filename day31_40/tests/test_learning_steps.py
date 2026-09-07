from __future__ import annotations

from types import SimpleNamespace

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from day31_40.production_graph import (
    ProductionServices, QualityDecision, RouteDecision, WorkItem,
)
from day31_40.step01_reliable_routing import build_graph as build01, initial_state as state01
from day31_40.step02_planning_observability import build_graph as build02, initial_state as state02
from day31_40.step03_persistence_hitl import build_graph as build03, initial_state as state03
from day31_40.step04_evidence_generation import build_graph as build04, initial_state as state04
from day31_40.step05_supervisor_mcp import build_graph as build05, initial_state as state05
from day31_40.adapters import upsert_candidate_car


class FakeLlm:
    def invoke(self, prompt):
        return SimpleNamespace(content="模型生成结果 [1]")


class FakeModel:
    llm = FakeLlm()

    def route(self, question: str, history_view: str):
        if "信息不足" in question:
            return RouteDecision(intent="public_info", sources=["web"],
                                 missing_information=["购车预算", "所在城市"], reason="test")
        if "越界" in question:
            return RouteDecision(intent="chitchat", sources=[], in_scope=False, reason="test")
        if "受限" in question:
            return RouteDecision(intent="calculation", sources=["mcp"],
                                 requires_approval=True, reason="test")
        if "多专家" in question:
            return RouteDecision(intent="calculation", sources=["web", "mcp"], reason="test")
        if "搜索" in question:
            return RouteDecision(intent="public_info", sources=["web"], reason="test")
        return RouteDecision(intent="family_data", sources=["sql"], reason="test")

    def plan(self, question: str, decision: RouteDecision):
        sources = decision.sources or ["web"]
        return [WorkItem(id=f"task-{i}", source=sources[(i - 1) % len(sources)],
                         instruction=f"步骤 {i}：{question}", parallel_group=0)
                for i in range(1, 3)]

    def generate(self, question: str, history_view: str, context: str, feedback: str):
        return f"基于证据回答 [1]：{context}"

    def review(self, question: str, context: str, draft: str):
        return QualityDecision(action="pass", score=90, feedback="通过")

    def summarize_history(self, old_history, existing: str):
        return existing + f"摘要{len(old_history)}轮"

    def generate_sql(self, question: str, schema: str):
        return ("SELECT candidate_name, powertrain, guide_price_yuan "
                "FROM candidate_cars ORDER BY guide_price_yuan LIMIT 10")


class Adapter:
    def __init__(self, source: str):
        self.source = source

    def collect(self, instruction: str):
        return [{"source": self.source, "title": f"{self.source} evidence",
                 "content": "真实适配器的测试替身", "reference": f"{self.source}://test"}]


def test_step01_only_routes_looks_up_and_answers():
    result = build01(FakeModel(), Adapter("web")).invoke(state01("搜索购车预算为什么不能只看指导价？"))
    assert result["route"]["sources"] == ["web"]
    assert result["evidence"]
    assert result["final_answer"] == "模型生成结果 [1]"


def test_step01_business_route_can_clarify_reject_scope_and_block_action():
    app = build01(FakeModel(), Adapter("web"))
    clarify = app.invoke(state01("信息不足的购车请求"))
    assert "购车预算" in clarify["final_answer"] and not clarify["evidence"]
    out = app.invoke(state01("越界请求"))
    assert "只处理家庭购车" in out["final_answer"]
    restricted = app.invoke(state01("受限的付款请求"))
    assert "不能执行下单" in restricted["final_answer"]


def test_step02_executes_plan_with_visible_cursor():
    result = build02(FakeModel()).invoke(state02("分两步比较家庭候选车"))
    assert result["completed_items"] == ["task-1", "task-2"]
    assert len(result["evidence"]) == 2
    assert [event["node"] for event in result["trace"]].count("specialist") == 2


def test_step03_pauses_and_resumes():
    config = {"configurable": {"thread_id": "step03-test"}}
    app = build03(FakeModel(), InMemorySaver())
    paused = app.invoke(state03("准备发布家庭购车建议"), config)
    assert "__interrupt__" in paused
    final = app.invoke(Command(resume="approve"), config)
    assert final["approval_status"] == "approved"
    assert final["conversation_history"]


def test_step04_runs_real_safe_sql_path_before_generation(tmp_path, monkeypatch):
    db = tmp_path / "car_decision.db"
    monkeypatch.setenv("DAY31_40_DB", str(db))
    upsert_candidate_car(db, {
        "candidate_name": "测试候选车", "powertrain": "bev", "guide_price_yuan": 188000,
        "energy_use_per_100km": 15, "energy_unit": "kWh",
        "insurance_per_year_yuan": 7000, "maintenance_per_year_yuan": 900,
        "resale_value_after_5y_yuan": 72000, "source_url": "https://example.test/car",
        "verified_at": "2026-08-26T00:00:00+08:00",
    })
    result = build04(FakeModel()).invoke(state04("查询候选车价格"))
    assert result["evidence"][0]["source"] == "sql"
    assert "188000.0" in result["context"]
    assert "[1]" in result["final_answer"]


def test_step05_supervisor_fans_out_to_isolated_specialists():
    services = ProductionServices(
        model=FakeModel(), adapters={source: Adapter(source) for source in ["web", "sql", "mcp"]}
    )
    result = build05(services).invoke(state05("多专家完成任务"), {"recursion_limit": 20})
    assert {item.rsplit(":", 1)[-1] for item in result["completed_items"]} == {"task-1", "task-2"}
    assert {item["source"] for item in result["evidence"]} == {"web", "mcp"}
    assert result["supervisor_steps"] == 2
    assert result["final_answer"]


def test_step05_early_exits_keep_the_user_facing_answer():
    services = ProductionServices(
        model=FakeModel(), adapters={source: Adapter(source) for source in ["web", "sql", "mcp"]}
    )
    app = build05(services)
    clarify = app.invoke(state05("信息不足的购车请求"))
    assert "购车预算" in clarify["final_answer"]
    out = app.invoke(state05("越界请求"))
    assert "只处理家庭购车" in out["final_answer"]


def test_step05_defers_approval_and_preserves_degraded_warning():
    class DegradedMcp(Adapter):
        def collect(self, instruction: str):
            return [{"source": "mcp", "title": "mcp 暂不可用", "content": "没有真实结果",
                     "reference": "unavailable://mcp", "warning": "degraded"}]

    services = ProductionServices(
        model=FakeModel(), adapters={"web": Adapter("web"), "sql": Adapter("sql"),
                                     "mcp": DegradedMcp("mcp")}
    )
    result = build05(services).invoke(state05("受限的付款请求"), {"recursion_limit": 20})
    assert result["completed_items"]
    assert "警告：degraded" in result["context"]
    assert result["final_answer"]
