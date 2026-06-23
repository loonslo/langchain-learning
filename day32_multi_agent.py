"""
Day 32 · 多 Agent 编排：supervisor 路由
==========================================================
测试工程师转 AI 应用开发

单个 Agent 啥都干，prompt 会臃肿、容易乱。复杂任务常拆成几个"专才" Agent，
再加一个 supervisor（主管）决定每一步交给谁。这节用原生 LangGraph 手搭一个
最小 supervisor：主管在 researcher / writer 之间路由，直到任务完成。

（不用第三方 langgraph-supervisor 库，用 StateGraph 手搭，理解机制更重要。）
==========================================================
"""

from typing import TypedDict, Literal
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from common import get_llm

llm = get_llm(temperature=0)


class State(TypedDict):
    task: str
    notes: str       # researcher 产出
    article: str     # writer 产出
    next: str        # supervisor 的决定


def supervisor(state: State) -> dict:
    """主管：看现在缺什么，决定下一步交给谁（researcher / writer / FINISH）。"""
    have_notes = bool(state.get("notes"))
    have_article = bool(state.get("article"))
    prompt = ChatPromptTemplate.from_template(
        "任务：{task}\n已有资料：{n}\n已有成文：{a}\n"
        "只回一个词决定下一步：没资料就回 researcher，有资料没成文就回 writer，都有了回 FINISH。"
    )
    decision = (prompt | llm | StrOutputParser()).invoke({
        "task": state["task"], "n": have_notes, "a": have_article}).strip()
    # 兜底：模型偶尔多话，按规则纠正
    if not have_notes:
        decision = "researcher"
    elif not have_article:
        decision = "writer"
    else:
        decision = "FINISH"
    print(f"  [supervisor] 下一步 → {decision}")
    return {"next": decision}


def researcher(state: State) -> dict:
    out = (ChatPromptTemplate.from_template("围绕「{task}」列 3 条关键资料点，简短")
           | llm | StrOutputParser()).invoke({"task": state["task"]})
    print("  [researcher] 产出资料")
    return {"notes": out}


def writer(state: State) -> dict:
    out = (ChatPromptTemplate.from_template("根据资料写一段 100 字短文。\n资料：{n}")
           | llm | StrOutputParser()).invoke({"n": state["notes"]})
    print("  [writer] 产出成文")
    return {"article": out}


def route(state: State) -> Literal["researcher", "writer", "__end__"]:
    return END if state["next"] == "FINISH" else state["next"]


def build_app():
    g = StateGraph(State)
    g.add_node("supervisor", supervisor)
    g.add_node("researcher", researcher)
    g.add_node("writer", writer)
    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", route,
                            {"researcher": "researcher", "writer": "writer", END: END})
    # 每个专才干完都回 supervisor，让它决定下一步（典型 supervisor 模式）
    g.add_edge("researcher", "supervisor")
    g.add_edge("writer", "supervisor")
    return g.compile()


if __name__ == "__main__":
    app = build_app()
    result = app.invoke(
        {"task": "介绍 RAG 的优点", "notes": "", "article": "", "next": ""},
        {"recursion_limit": 15},
    )
    print("\n最终成文：\n", result["article"])


# ----------------------------------------------------------
# 小结：
# - 多 Agent：把大任务拆给"专才"，supervisor 负责路由调度，各干各的更可控。
# - 原生实现：supervisor 节点出决定 → 条件边分发 → 专才干完回 supervisor，循环到 FINISH。
# - 何时上多 Agent：单 Agent 的 prompt/工具已经臃肿到互相打架时；否则别过度设计。
#
# 了解（同类框架，会比较即可）：
#   - AutoGen（微软）：对话式多 Agent，Agent 之间互相发消息协作
#   - CrewAI：给每个 Agent 设"角色 + 目标"，偏流程编排
#   - 和 LangGraph 区别：LangGraph 更底层、把控制流当图来精确控制
#
# 动手练习：加第三个专才 reviewer，在 writer 之后审一遍、不合格打回 writer。
# ----------------------------------------------------------
