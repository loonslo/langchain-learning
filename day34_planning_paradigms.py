"""
Day 34 · 其他规划范式（了解）+ multi-agent 框架定位
==========================================================
测试工程师转 AI 应用开发 · 阶段3　【了解】为主，别陷进去

Day32 ReAct（边想边做）、Day33 Plan-and-Execute（先规划再执行）是两个动手主力。
这天把其余规划范式和多 Agent 框架过一遍——面试能说清"何时用哪个"即可，不动手深做。

本文件是"能讲清"的速查，不调模型；末尾给一个最小 supervisor 路由骨架示意多 Agent 怎么编排。
==========================================================
"""

PLANNING_PARADIGMS = {
    "ReAct": "想→做→看 循环，走一步看一步。灵活、能纠错，但步数多、易跑偏、费 token。"
             "适合：工具多、路径不确定的探索性任务。（Day32 已动手）",
    "Plan-and-Execute": "先一次性规划出完整步骤，再逐步执行。可控、省 LLM 往返，"
                        "但计划错了整条错。适合：步骤相对确定、要省成本的任务。（Day33 已动手）",
    "Reflexion": "执行后让模型自我反思、把失败教训写进记忆，下次重试更好。"
                 "适合：可多次试错、有明确成败信号的任务（如刷题、代码修复）。",
    "ReWOO": "把推理和工具调用解耦：先一次规划出所有要调的工具（不等结果），"
             "再并行取证、最后汇总。省 LLM 调用、延迟低。适合：工具调用可并行的任务。",
    "Tree of Thoughts": "把'思路'展开成树，多条候选路径并行探索 + 回溯选最优。"
                        "强但极费算力。适合：解空间大、需要搜索的难题（如数独、规划）。",
}

MULTI_AGENT_FRAMEWORKS = {
    "LangGraph": "图描述状态机，最可控、可观测、可持久化。本课主力，适合要上生产、要评测的场景。",
    "AutoGen": "微软的多 Agent 对话框架，Agent 之间对话协作。研究/原型快，可控性弱于 LangGraph。",
    "CrewAI": "把 Agent 包成'角色+任务'的团队（role/task/crew），上手快、抽象高，"
              "灵活度和可观测性不如 LangGraph。",
    "A2A": "Agent-to-Agent 通信协议（前沿）。解决不同厂商/团队的 Agent 怎么互相发现和通信，"
           "和 MCP（Agent↔工具）是不同层。能聊即可，别深做。",
}


def supervisor_sketch():
    """最小 supervisor 路由骨架（不调模型，示意多 Agent 怎么编排）：
    一个 supervisor 节点按任务类型把活分给不同专家 Agent，再汇总。"""
    return (
        "START → supervisor →(条件路由)→ {research_agent / writer_agent / sql_agent}\n"
        "          ↑__________________ 各 agent 干完回 supervisor，直到任务完成 → END\n"
        "要点：supervisor 是一个会'决定下一步交给谁'的节点，本质还是 LangGraph 的条件边。"
    )


if __name__ == "__main__":
    print("===== 规划范式：何时用哪个 =====")
    for k, v in PLANNING_PARADIGMS.items():
        print(f"\n[{k}]\n  {v}")
    print("\n===== multi-agent 框架定位 =====")
    for k, v in MULTI_AGENT_FRAMEWORKS.items():
        print(f"\n[{k}]\n  {v}")
    print("\n===== supervisor 多 Agent 编排骨架 =====")
    print(supervisor_sketch())
    print("\n面试一句话：ReAct 灵活探索、Plan-Execute 可控省钱、Reflexion 能反思重试、"
          "ReWOO/ToT 各有省调用/强搜索的取舍；多 Agent 我用 LangGraph supervisor，可控可观测。")
