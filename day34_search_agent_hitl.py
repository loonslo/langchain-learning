"""
Day 34 · 阶段3 综合项目（下）：加 HITL + 持久化，端到端
==========================================================
测试工程师转 AI 应用开发  ← 阶段3 收尾作品

在 Day33 的搜索 Agent 上补两块"生产味"的能力，做成能讲的作品：
1. checkpoint 持久化：按 thread_id 记住会话，可多轮、可中断恢复（Day28）
2. human-in-the-loop：把最终答案"发布/采纳"前，先 interrupt 让人审一眼（Day30）
   ——模拟真实场景里"AI 起草、人确认"的把关流程。

这里用原生 StateGraph 手搭（而不是 create_react_agent），因为要在流程里
插入自定义的"人工审批"节点——这正是手搭图比现成 Agent 灵活的地方。

依赖（可选）：pip install ddgs
==========================================================
"""

from typing import TypedDict
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from common import get_llm

llm = get_llm(temperature=0)


class State(TypedDict):
    question: str
    search_result: str
    draft: str
    final: str


def search(state: State) -> dict:
    q = state["question"]
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            hits = list(ddgs.text(q, max_results=3))
        result = "\n".join(f"- {h['title']}：{h['body'][:120]}" for h in hits) if hits else ""
    except Exception:
        result = ""
    if not result:
        result = f"（离线示例）关于「{q}」的模拟搜索结果。"
    print("  [search] 拿到搜索结果")
    return {"search_result": result}


def summarize(state: State) -> dict:
    draft = (ChatPromptTemplate.from_template(
        "根据搜索结果回答问题，简洁中文。\n问题：{q}\n结果：{r}")
        | llm | StrOutputParser()).invoke({"q": state["question"], "r": state["search_result"]})
    print("  [summarize] 生成草稿")
    return {"draft": draft}


def human_review(state: State) -> dict:
    """发布前人工把关：interrupt 暂停，人 approve 就采纳，reject 就退回。"""
    decision = interrupt({"draft": state["draft"], "ask": "采纳这个答案吗？yes / no"})
    if str(decision).lower() == "yes":
        return {"final": state["draft"]}
    return {"final": "（人工驳回，需重做）"}


def build_app():
    g = StateGraph(State)
    g.add_node("search", search)
    g.add_node("summarize", summarize)
    g.add_node("human_review", human_review)
    g.add_edge(START, "search")
    g.add_edge("search", "summarize")
    g.add_edge("summarize", "human_review")
    g.add_edge("human_review", END)
    return g.compile(checkpointer=InMemorySaver())   # HITL + 多轮都靠它


if __name__ == "__main__":
    app = build_app()
    cfg = {"configurable": {"thread_id": "proj-1"}}

    out = app.invoke({"question": "RAG 和微调怎么选？", "search_result": "",
                      "draft": "", "final": ""}, cfg)
    pause = out["__interrupt__"][0].value
    print("\n草稿待人工确认：\n", pause["draft"][:120], "...")

    final = app.invoke(Command(resume="yes"), cfg)
    print("\n采纳后的最终答案：\n", final["final"][:160])


# ----------------------------------------------------------
# 小结（阶段3 收尾，能写进简历的作品）：
# - 串起来了：搜索工具 + LLM 总结 + checkpoint 持久化 + human-in-the-loop 审批。
# - 手搭图的价值：能在流程任意位置插自定义节点（这里是人工审批），现成 Agent 做不到。
# - 简历讲法：搜索→总结→人工把关的可控 Agent，高风险输出前必过人工，全程轨迹可查。
#
# 动手练习：human_review 返回"no"时，连一条边回 summarize 让它带反馈重写，而不是直接结束。
# ----------------------------------------------------------
