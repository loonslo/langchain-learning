"""
Day 30 · 用 LangGraph 重写工具调用（对比 day05 手写循环）
==========================================================
测试工程师转 AI 应用开发

day05 的工具调用是手写 while 循环：调模型 → 看有没有要调的工具 → 调工具 →
把结果塞回去 → 再调模型……自己管循环、管消息拼接，容易写错。
LangGraph 把这套"想→做→把结果带回来再想"做成标准图，几行就搭好。

核心套路（记牢，后面所有 Agent 都是它的变体）：
  agent 节点（调模型）──有 tool_calls?──→ tools 节点（执行工具）──→ 回 agent
                          └── 没有 ──→ END
这就是 ReAct 循环的骨架（Day26 正式讲 ReAct）。

用到：
- MessagesState：内置 state，只有一个 messages 列表，自动累加消息
- ToolNode：现成的"执行工具"节点，不用自己解析 tool_calls
- tools_condition：现成的路由——有 tool_calls 就去 tools，否则 END
==========================================================
"""

from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from common import get_llm


# ---------- 1. 定义工具（@tool 装饰普通函数即可）----------
@tool
def add(a: int, b: int) -> int:
    """计算两个整数相加。"""
    return a + b


@tool
def get_weather(city: str) -> str:
    """查询某城市天气（演示用，返回假数据）。"""
    return f"{city}今天晴，26℃"


TOOLS = [add, get_weather]


# ---------- 2. agent 节点：调带工具的模型 ----------
def build_app():
    llm = get_llm(temperature=0)
    llm_with_tools = llm.bind_tools(TOOLS)   # 告诉模型有哪些工具可用

    def agent(state: MessagesState) -> dict:
        # 把目前所有消息发给模型，模型可能直接答、也可能要求调用工具
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    g = StateGraph(MessagesState)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(TOOLS))     # 现成节点：执行模型要求的工具
    g.add_edge(START, "agent")
    # tools_condition：模型要调工具→去"tools"，否则→END
    g.add_conditional_edges("agent", tools_condition)
    g.add_edge("tools", "agent")             # 工具结果带回 agent，再想一轮
    return g.compile()


if __name__ == "__main__":
    app = build_app()
    for q in ["12 加 30 等于多少？", "北京天气怎么样？"]:
        print(f"\n问：{q}")
        result = app.invoke({"messages": [("user", q)]})
        print("答：", result["messages"][-1].content)


# ----------------------------------------------------------
# 小结：
# - day05 手写的"调模型→执行工具→回灌"循环，LangGraph 用 agent↔tools 两节点 + 条件边搞定。
# - MessagesState 自动累加对话消息；ToolNode 自动执行 tool_calls；tools_condition 自动路由。
# - 这张 agent↔tools 循环图，就是后面 ReAct / 各种工具 Agent 的通用骨架。
#
# 对比 day05：少写了循环控制、消息拼接、tool_call 解析——更不容易出错，也更好加 checkpoint。
#
# 动手练习：加一个 @tool multiply，问"3 乘以 4 再加 5"，看模型会不会连续调两个工具。
# ----------------------------------------------------------
