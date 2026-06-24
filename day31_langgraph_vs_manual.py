"""
Day 31 · 用 LangGraph 重写工具调用（完成）+ 对比手写循环
==========================================================
测试工程师转 AI 应用开发 · 阶段3

Day30 把工具调用主流程用 LangGraph 搭起来了。这天补全多轮 + 记忆（挂 checkpointer），
再和 Day05/Day10 的手写 while 循环对比，讲清"LangGraph 到底替我做了什么"。

对比的意义：你能说清框架替你包掉的那层（harness），面试就比"会用 LangGraph"高一档。
==========================================================
"""

from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from common import get_llm


@tool
def add(a: int, b: int) -> int:
    """计算 a + b。"""
    return a + b


TOOLS = [add]


def build():
    llm = get_llm(temperature=0).bind_tools(TOOLS)

    def agent(state: MessagesState) -> dict:
        return {"messages": [llm.invoke(state["messages"])]}

    g = StateGraph(MessagesState)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)   # 有 tool_calls 就去 tools，否则结束
    g.add_edge("tools", "agent")                        # 工具结果回灌，循环
    return g.compile(checkpointer=InMemorySaver())       # 挂 checkpointer = 多轮记忆


# 手写循环替你做的那些事，框架内置了 —— 对比表
COMPARISON = """
| 关注点            | 手写循环（Day05/Day10）          | LangGraph（本文件）              |
|------------------|----------------------------------|----------------------------------|
| 判断要不要调工具  | 自己解析 tool_calls + if 判断     | tools_condition 内置             |
| 执行工具+回灌结果 | 自己拼 ToolMessage 塞回 messages  | ToolNode 自动                    |
| 循环控制          | 自己 while + 自己防死循环         | 图的边 + recursion_limit         |
| 多轮记忆          | 自己维护 messages 列表            | checkpointer 按 thread_id 自动   |
| 中断/恢复/HITL    | 几乎没法做                        | interrupt + checkpointer 内置    |
结论：框架替我包掉的 = 工具解析、循环、记忆、中断恢复——这层就是 harness。
"""


if __name__ == "__main__":
    app = build()
    cfg = {"configurable": {"thread_id": "t1"}}
    r1 = app.invoke({"messages": [("user", "帮我算 18 加 24")]}, cfg)
    print("第1轮：", r1["messages"][-1].content)
    r2 = app.invoke({"messages": [("user", "再加 100 呢")]}, cfg)   # 靠记忆理解"再加"
    print("第2轮（带记忆）：", r2["messages"][-1].content)
    print(COMPARISON)
