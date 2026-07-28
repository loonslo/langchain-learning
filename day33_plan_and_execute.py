"""
Day 33 · 规划范式速查 + Plan-and-Execute 动手
==========================================================
测试工程师转 AI 应用开发

【一】范式速查：几种主流"Agent 怎么思考/规划"，面试能说清"何时用哪个"：
    ReAct / Plan-and-Execute / Reflexion / ReWOO / Tree of Thoughts。
    多 Agent 框架定位（LangGraph/AutoGen/CrewAI/A2A）一并过。

【二】动手：Plan-and-Execute。先让模型把任务拆成有序步骤清单（plan），
    再一步步执行（execute），执行完划掉。计划显式、过程可控、便于审计。
    ReAct（单 Agent 循环）见 Day30；Supervisor 多 Agent 见 Day39。

衔接：Day30/Day32 是单 Agent ReAct；这里先规划再执行；Day39 多 Agent 协作。
==========================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()   # 读 .env 里的 DEEPSEEK_API_KEY


# —— 内联 LLM 工厂：本文件自包含，不依赖 common.py，方便单独阅读 ——
def get_llm(temperature: float = 0.0, model: str = "deepseek-chat", **kwargs):
    """DeepSeek 对话模型（OpenAI 兼容）。temperature=0 → 输出可复现。"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temperature,
        **kwargs,
    )


llm = get_llm(temperature=0)


# ============================================================
# 【一】规划范式 + 多 Agent 框架 速查（不调模型）
# ============================================================
PLANNING_PARADIGMS = {
    "ReAct": "想→做→看 循环，走一步看一步。灵活、能纠错，但步数多、易跑偏、费 token。"
             "适合：工具多、路径不确定的探索性任务。（Day30/Day32 已动手）",
    "Plan-and-Execute": "先一次性规划出完整步骤，再逐步执行。可控、省 LLM 往返，"
                        "但计划错了整条错。适合：步骤相对确定、要省成本的任务。（本文件动手）",
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
    一个 supervisor 节点按任务类型把活分给不同专家 Agent，再汇总。
    完整可运行版见 Day39（supervisor 多 Agent + Fan-out）。"""
    return (
        "START → supervisor →(条件路由)→ {research_agent / writer_agent / sql_agent}\n"
        "          ↑__________________ 各 agent 干完回 supervisor，直到任务完成 → END\n"
        "要点：supervisor 是一个会'决定下一步交给谁'的节点，本质还是 LangGraph 的条件边。"
    )


# ============================================================
# 【二】Plan-and-Execute 实现
# ============================================================
class State(TypedDict):
    task: str            # 总任务
    plan: list[str]      # 步骤清单
    done: list[str]      # 已完成步骤的结果
    cursor: int          # 当前执行到第几步


def planner(state: State) -> dict:
    """让模型把任务拆成 2-4 个有序步骤，每行一个。"""
    prompt = ChatPromptTemplate.from_template(
        "把下面的任务拆成 2-4 个有序、可执行的步骤，每行一个，不要编号、不要多余解释：\n{task}"
    )
    text = (prompt | llm | StrOutputParser()).invoke({"task": state["task"]})
    steps = [s.strip("-· ").strip() for s in text.splitlines() if s.strip()]
    print("规划出的步骤：")
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s}")
    return {"plan": steps, "done": [], "cursor": 0}


def executor(state: State) -> dict:
    """执行当前这一步，结果追加到 done，cursor 前移。"""
    step = state["plan"][state["cursor"]]
    prompt = ChatPromptTemplate.from_template(
        "围绕总任务「{task}」，完成这一步并简要给出结果：{step}"
    )
    out = (prompt | llm | StrOutputParser()).invoke(
        {"task": state["task"], "step": step})
    print(f"\n执行第{state['cursor']+1}步：{step}\n  → {out[:80]}...")
    return {"done": state["done"] + [out], "cursor": state["cursor"] + 1}


def has_more(state: State) -> str:
    """还有没执行完的步骤就继续，否则结束。"""
    return "more" if state["cursor"] < len(state["plan"]) else "finish"


def build_app():
    g = StateGraph(State)
    g.add_node("planner", planner)
    g.add_node("executor", executor)
    g.add_edge(START, "planner")
    g.add_edge("planner", "executor")
    g.add_conditional_edges("executor", has_more, {"more": "executor", "finish": END})
    return g.compile()


if __name__ == "__main__":
    print("===== 【一】规划范式：何时用哪个 =====")
    for k, v in PLANNING_PARADIGMS.items():
        print(f"\n[{k}]\n  {v}")
    print("\n===== 多 Agent 框架定位 =====")
    for k, v in MULTI_AGENT_FRAMEWORKS.items():
        print(f"\n[{k}]\n  {v}")
    print("\n===== supervisor 多 Agent 编排骨架（完整版见 Day39）=====")
    print(supervisor_sketch())
    print("\n面试一句话：ReAct 灵活探索、Plan-Execute 可控省钱、Reflexion 能反思重试、"
          "ReWOO/ToT 各有省调用/强搜索的取舍；多 Agent 我用 LangGraph supervisor，可控可观测。")

    print("\n===== 【二】Plan-and-Execute 动手 =====")
    app = build_app()
    # recursion_limit 给足，避免步骤多时被安全阀拦下
    result = app.invoke(
        {"task": "为一篇介绍 RAG 的科普短文做准备", "plan": [], "done": [], "cursor": 0},
        {"recursion_limit": 20},
    )
    print(f"\n全部 {len(result['done'])} 步执行完毕。")


# ----------------------------------------------------------
# 小结：
# - Plan-and-Execute：planner 先出清单，executor 按 cursor 逐步做，条件边控制"还有没有"。
# - 比 ReAct 更可控、更可审计（计划显式、做到第几步清楚），适合多步、确定性强的任务。
# - 缺点：计划一旦错了后面全错；进阶版会在执行中"重新规划"（replan）。
# - 面试常问：ReAct vs Plan-and-Execute？（ReAct 走一步看一步灵活但费 token；
#   Plan-Execute 先规划全程再执行，可控省钱但计划错了全错。）
#
# 动手练习：给 State 加一个 replan 节点——执行到一半让模型根据已完成结果修订剩余步骤。
# ----------------------------------------------------------
