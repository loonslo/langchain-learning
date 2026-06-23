"""
Day 28 · 状态持久化：checkpoint + 多轮记忆
==========================================================
测试工程师转 AI 应用开发

前面的图每次 invoke 都是"一锤子买卖"，跑完 state 就没了——换句话说没有记忆。
LangGraph 的 checkpointer 能在每一步自动存 state 快照，按 thread_id 区分会话。
好处：
1. 多轮记忆：同一个 thread_id 续聊，自动带上历史（不用自己拼 messages）
2. 中断恢复：程序挂了/人工打断后，能从上次的 checkpoint 接着跑（Day30 HITL 靠它）
3. 多用户隔离：不同 thread_id 各记各的

这节把 day25 的工具 Agent 加上 InMemorySaver，验证"它记得上一句"。
（InMemorySaver 存在内存，重启即丢；生产用 SqliteSaver/PostgresSaver 落盘。）
==========================================================
"""

from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from common import get_llm


@tool
def get_weather(city: str) -> str:
    """查询城市天气（演示假数据）。"""
    return f"{city}今天晴，25℃"


TOOLS = [get_weather]


def build_app():
    llm_with_tools = get_llm(temperature=0).bind_tools(TOOLS)

    def agent(state: MessagesState) -> dict:
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    g = StateGraph(MessagesState)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)
    g.add_edge("tools", "agent")
    # 关键：编译时挂上 checkpointer，图就有了"记忆"
    return g.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    app = build_app()
    # thread_id 标识一个会话；同一个 id 续聊会自动带历史
    cfg = {"configurable": {"thread_id": "user-1"}}

    print("第1轮：")
    r1 = app.invoke({"messages": [("user", "北京天气怎么样？")]}, cfg)
    print("  答：", r1["messages"][-1].content)

    print("\n第2轮（只说'那上海呢'，靠记忆理解是在问天气）：")
    r2 = app.invoke({"messages": [("user", "那上海呢？")]}, cfg)
    print("  答：", r2["messages"][-1].content)

    print("\n换一个 thread_id（新会话，没有上面的记忆）：")
    r3 = app.invoke({"messages": [("user", "那上海呢？")]},
                    {"configurable": {"thread_id": "user-2"}})
    print("  答：", r3["messages"][-1].content)


# ----------------------------------------------------------
# 小结：
# - checkpointer 自动存每步 state 快照，按 thread_id 隔离会话——这就是"记忆"的来源。
# - 同一 thread_id 续聊自动带历史；换 id 即全新会话。比 day04 手动拼 messages 干净得多。
# - InMemorySaver 内存版（重启丢）；生产换 SqliteSaver / PostgresSaver 落盘。
# - 中断恢复也靠它：state 存着，随时能接着跑——Day30 的人工审批就建立在这上面。
#
# 动手练习：把 InMemorySaver 换成 SqliteSaver（langgraph-checkpoint-sqlite），
#          跑完重启程序，用同一 thread_id 看是否还记得。
# ----------------------------------------------------------
