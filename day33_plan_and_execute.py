"""
Day 33 · Plan-and-Execute：先规划，再逐步执行
==========================================================
测试工程师转 AI 应用开发

ReAct 是"走一步看一步"，复杂任务容易绕路、步数失控。
Plan-and-Execute 换思路：先让模型把任务拆成一个有序步骤清单（plan），
再一步步执行（execute），执行完一步就从清单里划掉。计划显式、过程可控、
也方便记录"做到第几步"——对要审计/可观测的系统更友好。

本节用 LangGraph 手搭一个最小版：
  planner（出步骤清单）→ executor（做一步）──还有剩？──→ executor（继续）
                                              └── 没了 ──→ END
为聚焦"规划→执行"骨架，执行这里用 LLM 直接回答每个子步骤（不接真工具）。
==========================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from common import get_llm

llm = get_llm(temperature=0)


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
#
# 动手练习：给 State 加一个 replan 节点——执行到一半让模型根据已完成结果修订剩余步骤。
# ----------------------------------------------------------
