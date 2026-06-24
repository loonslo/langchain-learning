"""
Day 35 · 状态持久化（checkpoint）+ 上下文管理
==========================================================
测试工程师转 AI 应用开发

两件让 Agent 能上真实场景的事：

1. 状态持久化（checkpoint/persistence）：前面的图每次 invoke 跑完 state 就没了，
   等于没记忆。LangGraph 的 checkpointer 每步自动存 state 快照，按 thread_id 隔离会话。
   - 多轮记忆：同一 thread_id 续聊自动带历史，不用手拼 messages；
   - 中断恢复：挂了/被打断后从上次 checkpoint 接着跑（Day36 HITL 就靠它）；
   - 多用户隔离：不同 thread_id 各记各的。
   InMemorySaver 存内存（重启即丢）；生产换 SqliteSaver / PostgresSaver 落盘。

2. 上下文管理（Context Engineering）：对话越长 messages 越多，迟早超窗口、越来越贵。
   常见策略：只留最近 N 轮 + 把更早的压成一段摘要。关键是"该留的事实别在摘要里丢"。
==========================================================
"""

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from common import get_llm

llm = get_llm(temperature=0)


# ============ 第一部分：checkpoint 持久化 + 多轮记忆 ============
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
    # 关键：compile 时挂 checkpointer，图就有了"记忆"
    return g.compile(checkpointer=InMemorySaver())


def demo_memory():
    app = build_app()
    cfg = {"configurable": {"thread_id": "user-1"}}   # thread_id 标识一个会话
    print("第1轮：")
    r1 = app.invoke({"messages": [("user", "北京天气怎么样？")]}, cfg)
    print("  答：", r1["messages"][-1].content)
    print("第2轮（只说'那上海呢'，靠记忆理解在问天气）：")
    r2 = app.invoke({"messages": [("user", "那上海呢？")]}, cfg)
    print("  答：", r2["messages"][-1].content)
    print("换 thread_id（全新会话，无上面记忆）：")
    r3 = app.invoke({"messages": [("user", "那上海呢？")]},
                    {"configurable": {"thread_id": "user-2"}})
    print("  答：", r3["messages"][-1].content)


# ============ 第二部分：上下文裁剪 + 摘要压缩 ============
def compress_history(messages: list, keep_recent: int = 2) -> list:
    """保留最近 keep_recent 条，更早的压成一条摘要 SystemMessage。"""
    if len(messages) <= keep_recent:
        return messages
    old, recent = messages[:-keep_recent], messages[-keep_recent:]
    text = "\n".join(f"{type(m).__name__}: {m.content}" for m in old)
    summary = (ChatPromptTemplate.from_template(
        "用一两句话概括下面这段对话历史，保留关键事实：\n{h}"
    ) | llm | StrOutputParser()).invoke({"h": text})
    print(f"  [压缩] {len(old)} 条旧消息 → 1 条摘要：{summary[:50]}...")
    return [SystemMessage(content=f"对话历史摘要：{summary}")] + recent


def demo_context():
    history = [
        HumanMessage(content="我叫小王，在学 RAG"),
        AIMessage(content="好的小王，RAG 是检索增强生成"),
        HumanMessage(content="我之前是做测试的"),
        AIMessage(content="测试背景对 RAG 评测很有优势"),
        HumanMessage(content="那我现在叫什么名字？"),
    ]
    print("原始历史 5 条 → 压缩（保留最近 2 条 + 摘要）：")
    compressed = compress_history(history, keep_recent=2)
    print(f"  压缩后 {len(compressed)} 条")
    ans = llm.invoke(compressed).content   # 摘要里应保住"小王"
    print("  问'我叫什么'，模型答：", ans[:50])


if __name__ == "__main__":
    print("===== 1) checkpoint 持久化 + 多轮记忆 =====")
    demo_memory()
    print("\n===== 2) 上下文裁剪 + 摘要 =====")
    demo_context()


# ----------------------------------------------------------
# 小结：
# - checkpointer 按 thread_id 存每步 state 快照——多轮记忆 + 中断恢复都靠它，比 day04 手拼干净。
# - 上下文管理：留最近 N 轮 + 旧消息摘要，控 token、不超窗；别把名字/关键决定摘掉。
# - 动手练习：把 InMemorySaver 换 SqliteSaver 落盘重启验证；keep_recent 改 1 看摘要还保不保得住"小王"。
# ----------------------------------------------------------
