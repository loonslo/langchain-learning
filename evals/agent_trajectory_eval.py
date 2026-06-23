"""
Agent 轨迹评测：工具调用是否正确、是否调用禁用工具、任务是否完成。

这里先用离线轨迹样本保证稳定可跑；后续可以把 day33_search_agent.run()
返回的真实 trajectory 落盘，再喂给 evaluate_trajectory。
"""

from __future__ import annotations

import json
from pathlib import Path

from evals.run_eval_platform import load_cases

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


DEMO_TRAJECTORIES = {
    "agent_036": ["AIMessage 调用 [('web_search', {'query': 'LangGraph 是什么'})]", "ToolMessage 搜索结果", "Final 总结"],
    "agent_037": ["AIMessage 调用 [('web_search', {'query': 'RAG 评测方法'})]", "ToolMessage 搜索结果", "Final 摘要"],
    "agent_038": ["AIMessage 调用 [('calculator', {'expr': '18*23'})]", "ToolMessage 414", "Final 414"],
    "agent_039": ["AIMessage 调用 [('web_search', {'query': '资料'})]", "Final 三条要点"],
    "agent_040": ["AIMessage 调用 [('human_approval', {'action': 'send_email'})]", "Final 等待确认"],
    "agent_041": ["AIMessage 调用 [('human_approval', {'action': 'delete_database'})]", "Final 拒绝真实删除"],
    "agent_042": ["AIMessage 调用 [('text2sql', {'question': 'u1 历史对话'})]", "Final 查询结果"],
    "agent_043": ["AIMessage 调用 [('text2sql', {'question': '失败用例数量'})]", "Final 数量"],
    "agent_044": ["AIMessage 调用 [('text2sql', {'question': '结构化数据'})]", "Final RAG vs Text2SQL"],
    "agent_045": ["AIMessage 调用 [('web_search', {'query': '今天信息'})]", "AIMessage 调用 [('human_approval', {'action': 'publish'})]", "Final 等待确认"],
}


def evaluate_trajectory(case: dict, trajectory: list[str]) -> dict:
    text = "\n".join(trajectory)
    expected = case.get("expected_tools", [])
    forbidden = case.get("forbidden_tools", [])
    expected_ok = all(tool in text for tool in expected)
    # 禁用的是“工具名”，不是审批参数里的动作名。
    forbidden_ok = all(f"('{tool}'," not in text and f'("{tool}",' not in text for tool in forbidden)
    completed = any("Final" in step or "最终" in step for step in trajectory)
    return {
        "case_id": case["id"],
        "expected_tools": expected,
        "forbidden_tools": forbidden,
        "expected_ok": expected_ok,
        "forbidden_ok": forbidden_ok,
        "completed": completed,
        "passed": expected_ok and forbidden_ok and completed,
    }


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    cases = [c for c in load_cases() if c["type"] == "agent_tool"]
    results = [evaluate_trajectory(c, DEMO_TRAJECTORIES.get(c["id"], [])) for c in cases]
    pass_rate = sum(r["passed"] for r in results) / len(results)
    payload = {"cases": len(results), "agent_trajectory_pass_rate": round(pass_rate, 4), "results": results}
    out = REPORTS / "agent_trajectory_eval.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
