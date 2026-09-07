"""真实在线验收：显式加 --run-online 才运行，会真实消耗模型和搜索额度。"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

from day31_40.adapters import TavilySearchAdapter
from day31_40.production_graph import build_graph, build_online_services, initial_state


def require_online(request):
    if not request.config.getoption("--run-online"):
        pytest.skip("使用 --run-online 才执行真实外部调用")


@pytest.mark.online
def test_real_tavily_returns_url_and_content(request):
    require_online(request)
    assert os.getenv("TAVILY_API_KEY"), "缺少 TAVILY_API_KEY"
    rows = TavilySearchAdapter(max_results=1).collect("纯电汽车 家庭用车 安全 质保 最新资料")
    assert rows and rows[0]["reference"].startswith("http") and rows[0]["content"]


@pytest.mark.online
def test_real_mcp_server_exposes_tools_resources_and_prompts(request):
    require_online(request)

    async def probe():
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({
            "car_calculator": {
                "command": sys.executable,
                "args": [str(Path("day31_40/car_mcp_server.py").resolve())],
                "transport": "stdio",
                "env": {**os.environ, "DEMO_TOKEN": "secret-123",
                        "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
            }
        })
        tools = await client.get_tools(server_name="car_calculator")
        energy = next(tool for tool in tools if tool.name == "calculate_annual_energy_cost")
        result = await energy.ainvoke({"annual_mileage_km": 15000,
                                       "energy_use_per_100km": 15,
                                       "energy_price_yuan": 0.6})
        resources = await client.get_resources(
            "car_calculator", uris="config://car-decision-rules"
        )
        prompts = await client.get_prompt(
            "car_calculator", "car_purchase_analysis", arguments={"text": "比较三辆候选车"}
        )
        return tools, result, resources, prompts

    tools, result, resources, prompts = asyncio.run(probe())
    assert {tool.name for tool in tools} >= {
        "calculate_monthly_payment", "calculate_annual_energy_cost",
        "calculate_five_year_tco", "calculate_budget_ratio", "secure_ping",
    }
    assert "1350" in str(result)
    assert "不得自动下单" in resources[0].as_string()
    assert prompts


@pytest.mark.online
def test_real_deepseek_tavily_sql_and_mcp_work_together(request):
    require_online(request)
    assert os.getenv("DEEPSEEK_API_KEY"), "缺少 DEEPSEEK_API_KEY"
    assert os.getenv("TAVILY_API_KEY"), "缺少 TAVILY_API_KEY"

    app = build_graph(build_online_services())
    state = app.invoke(
        initial_state(
            "我们家预算 20 万，年行驶约 1.5 万公里，有家充。请搜索燃油、纯电和插混"
            "家庭用车的最新公开资料，查询家庭画像和候选车数据，并通过 MCP 计算月供、"
            "年度能源费与五年总持有成本，最后生成带引用的购车建议报告。",
            tenant_id="online-test",
        ),
        {"configurable": {"thread_id": "online-test:full"}, "recursion_limit": 40},
    )
    current = [e for e in state["evidence"] if e.get("request_id") == state["request_id"]]
    assert {e["source"] for e in current} == {"web", "sql", "mcp"}
    assert not any(e.get("reference", "").startswith("unavailable://") for e in current)
    assert state["quality"]["score"] >= 0
    assert len(state["final_answer"]) >= 80
