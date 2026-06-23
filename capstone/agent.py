"""
capstone/agent.py · Agent 层：把知识库当工具 + 高风险动作 HITL
==========================================================
整合 day25-34：用 LangGraph 搭一个会"自己决定查不查知识库"的 Agent，
并对高风险动作（这里以"对外发布答案"为例）加 human-in-the-loop 审批。
checkpointer 提供多轮记忆 + 暂停恢复。
==========================================================
"""

from typing import TypedDict
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

import config as C
from knowledge_base import KnowledgeBase


def build_agent(kb: KnowledgeBase):
    """返回一个带知识库工具 + 发布审批节点的图。"""
    chain = kb.chain()

    class State(TypedDict):
        question: str
        answer: str
        published: str

    def answer_node(state: State) -> dict:
        return {"answer": chain.invoke(state["question"])}

    def publish_gate(state: State) -> dict:
        # 高风险：把答案"对外发布"前，先让人审一眼（HITL）
        decision = interrupt({"answer": state["answer"], "ask": "确认发布？yes/no"})
        if str(decision).lower() == "yes":
            return {"published": state["answer"]}
        return {"published": "（人工驳回，未发布）"}

    g = StateGraph(State)
    g.add_node("answer", answer_node)
    g.add_node("publish_gate", publish_gate)
    g.add_edge(START, "answer")
    g.add_edge("answer", "publish_gate")
    g.add_edge("publish_gate", END)
    return g.compile(checkpointer=InMemorySaver())


# 也可把知识库暴露成标准 @tool，给通用 ReAct Agent 用（多工具场景）
def kb_tool(kb: KnowledgeBase):
    @tool
    def search_knowledge_base(question: str) -> str:
        """查询企业知识库回答问题，返回带来源的答案。"""
        return kb.answer(question)
    return search_knowledge_base


if __name__ == "__main__":
    kb = KnowledgeBase().build()
    app = build_agent(kb)
    cfg = {"configurable": {"thread_id": "demo"}}
    out = app.invoke({"question": "知识库讲了什么？", "answer": "", "published": ""}, cfg)
    print("待审答案：", out["__interrupt__"][0].value["answer"][:120])
    final = app.invoke(Command(resume="yes"), cfg)
    print("发布结果：", final["published"][:120])
