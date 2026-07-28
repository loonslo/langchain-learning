"""
Day 37 · 阶段3 综合项目：搜索+总结 Agent → 加 HITL + 持久化，端到端
==========================================================
测试工程师转 AI 应用开发  ← 阶段3 综合项目：把 Agent 知识串成一个能用的作品

【一】搜索+总结 Agent：搜索工具 + ReAct 循环 + 轨迹日志（每步想了啥、调了啥都记下来）。
    轨迹日志是测试背景的加分项——Agent 出错时，有完整轨迹才能定位"错在哪一步"。

【二】端到端收尾：在【一】的搜索 Agent 上补两块"生产味"的能力，做成能讲的作品：
    1. checkpoint 持久化：按 thread_id 记住会话，可多轮、可中断恢复（基于 Day35）
    2. human-in-the-loop：把最终答案"采纳"前先 interrupt 让人审一眼（基于 Day36）
       ——模拟真实场景里"AI 起草、人确认"的把关流程。
    这里用原生 StateGraph 手搭（而非 create_react_agent），因为要在流程里插入
    自定义"人工审批"节点——这正是手搭图比现成 Agent 灵活的地方。

依赖（可选）：pip install tavily-python   # 真联网搜索（.env 需 TAVILY_API_KEY，免费额度 1000 次/月）
             没装包或没配 key 则自动用内置假数据，逻辑照样跑
==========================================================
"""

from typing import TypedDict
from langchain_core.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
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


# —— 共用搜索函数：Tavily 专为 LLM 设计，返回干净摘要 + 来源 URL ——
def tavily_search(query: str, max_results: int = 3) -> str:
    """真联网搜索；失败（没装包/没 key/网络问题）返回空串，由调用方兜底。"""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        resp = client.search(query, max_results=max_results, timeout=10)
        # 截断每条内容防止爆上下文；带 URL 便于答案标注来源
        return "\n".join(
            f"- {r['title']}：{r['content'][:120]}（来源：{r['url']}）"
            for r in resp.get("results", [])
        )
    except Exception:
        return ""


# ============================================================
# 【一】搜索+总结 Agent（带轨迹日志）
# ============================================================
@tool
def web_search(query: str) -> str:
    """联网搜索一个问题，返回若干条结果摘要（含来源 URL）。"""
    result = tavily_search(query)
    if result:
        return result
    # 兜底假数据：没网/没装依赖也能演示 Agent 流程
    return f"（离线示例结果）关于「{query}」：这是一条模拟搜索摘要，用于演示总结流程。"


def build_search_agent():
    return create_react_agent(
        get_llm(temperature=0),
        tools=[web_search],
        prompt="你是研究助理。遇到需要事实/最新信息的问题，先用 web_search 搜，再用中文总结成简洁回答，并说明依据。",
    )


def run_search(question: str):
    agent = build_search_agent()
    print(f"问题：{question}\n--- 执行轨迹 ---")
    trajectory = []
    # stream 出每一步，边跑边记轨迹（便于排错与展示）
    for chunk in agent.stream({"messages": [("user", question)]}, stream_mode="values"):
        msg = chunk["messages"][-1]
        role = type(msg).__name__
        tc = getattr(msg, "tool_calls", None)
        if tc:
            line = f"[{role}] 调用 {[(c['name'], c['args']) for c in tc]}"
        else:
            line = f"[{role}] {str(msg.content)[:100]}"
        trajectory.append(line)
        print(" ", line)
    print("--- 轨迹共", len(trajectory), "步 ---")
    return trajectory


# ============================================================
# 【二】端到端：搜索 + 总结 + checkpoint + 人工审批
# ============================================================
llm = get_llm(temperature=0)


class ProjState(TypedDict):
    question: str
    search_result: str
    draft: str
    final: str


def search(state: ProjState) -> dict:
    q = state["question"]
    result = tavily_search(q)
    if not result:
        result = f"（离线示例）关于「{q}」的模拟搜索结果。"
    print("  [search] 拿到搜索结果")
    return {"search_result": result}


def summarize(state: ProjState) -> dict:
    draft = (ChatPromptTemplate.from_template(
        "根据搜索结果回答问题，简洁中文。\n问题：{q}\n结果：{r}")
        | llm | StrOutputParser()).invoke({"q": state["question"], "r": state["search_result"]})
    print("  [summarize] 生成草稿")
    return {"draft": draft}


def human_review(state: ProjState) -> dict:
    """发布前人工把关：interrupt 暂停，人 approve 就采纳，reject 就退回。"""
    decision = interrupt({"draft": state["draft"], "ask": "采纳这个答案吗？yes / no"})
    if str(decision).lower() == "yes":
        return {"final": state["draft"]}
    return {"final": "（人工驳回，需重做）"}


def build_proj():
    g = StateGraph(ProjState)
    g.add_node("search", search)
    g.add_node("summarize", summarize)
    g.add_node("human_review", human_review)
    g.add_edge(START, "search")
    g.add_edge("search", "summarize")
    g.add_edge("summarize", "human_review")
    g.add_edge("human_review", END)
    return g.compile(checkpointer=InMemorySaver())   # HITL + 多轮都靠它


if __name__ == "__main__":
    print("===== 【一】搜索+总结 Agent（轨迹日志）=====")
    run_search("LangGraph 适合用来做什么？")

    print("\n===== 【二】端到端：搜索 → 总结 → 人工审批 =====")
    app = build_proj()
    cfg = {"configurable": {"thread_id": "proj-1"}}
    out = app.invoke({"question": "RAG 和微调怎么选？", "search_result": "",
                      "draft": "", "final": ""}, cfg)
    pause = out["__interrupt__"][0].value
    print("\n草稿待人工确认：\n", pause["draft"][:120], "...")
    final = app.invoke(Command(resume="yes"), cfg)
    print("\n采纳后的最终答案：\n", final["final"][:160])


# ----------------------------------------------------------
# 小结（阶段3 收尾，能写进简历的作品）：
# - 【一】搜索+总结 Agent = 搜索工具 + ReAct 循环 + 让模型把结果总结成答案；
#   用 agent.stream(stream_mode="values") 拿每一步状态，记成轨迹日志。
# - 【二】串起来了：搜索工具 + LLM 总结 + checkpoint 持久化 + human-in-the-loop 审批。
# - 手搭图的价值：能在流程任意位置插自定义节点（这里是人工审批），现成 Agent 做不到。
# - 简历讲法：搜索→总结→人工把关的可控 Agent，高风险输出前必过人工，全程轨迹可查。
#
# 动手练习：human_review 返回"no"时，连一条边回 summarize 让它带反馈重写，而不是直接结束。
# ----------------------------------------------------------
