"""
Day 30 · ReAct Agent：手搭 agent↔tools 循环 + create_react_agent 一行版
==========================================================
测试工程师转 AI 应用开发

【第一部分·手搭】Day05 手写 while 循环调工具容易写错。LangGraph 把
"想→做→把结果带回来再想"做成标准图：
  agent 节点（调模型）──有 tool_calls?──→ tools 节点（执行工具）──→ 回 agent
                          └── 没有 ──→ END
这就是 ReAct 循环骨架。用到 MessagesState / ToolNode / tools_condition。

【第二部分·现成】这套骨架封装成 create_react_agent，一行就得到 ReAct Agent。
生产里常直接用它，省得每次手搭。其他规划范式见 Day33。

注（LangChain v1，2025-10 起）：官方推荐入口改为 langchain.agents.create_agent
（底层仍是 LangGraph），langgraph.prebuilt.create_react_agent 属旧入口、逐步弃用。
本节手搭部分不受影响——手搭学的就是 create_agent 内部那张图，面试讲这个更值钱。

衔接：Day29 打了分支/循环基础；Day39 升级到多 Agent（Supervisor）。
==========================================================
"""

from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
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


# ---------- 工具 ----------
@tool
def add(a: int, b: int) -> int:
    """计算两个整数相加。"""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """计算两个整数相乘。"""
    return a * b


@tool
def get_weather(city: str) -> str:
    """查询某城市天气（演示用，返回假数据）。"""
    return f"{city}今天晴，26℃"


TOOLS = [add, multiply, get_weather]


# ============================================================
# 第一部分：手搭 agent↔tools 循环
# ============================================================
def build_handmade():
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


# ============================================================
# 第二部分：create_react_agent 一行版
# ============================================================
def build_prebuilt():
    # 内部就是第一部分的 agent↔tools 图；生产常用它省事
    return create_react_agent(
        get_llm(temperature=0),
        tools=TOOLS,
        prompt="你是一个会用工具的助手。需要计算或查询时调用合适的工具，最后用中文回答。",
    )


if __name__ == "__main__":
    print("===== 手搭 ReAct Agent =====")
    app = build_handmade()
    for q in ["12 加 30 等于多少？", "北京天气怎么样？"]:
        print(f"\n问：{q}")
        result = app.invoke({"messages": [("user", q)]})
        print("答：", result["messages"][-1].content)

    print("\n===== create_react_agent 一行版（连续两步）=====")
    agent = build_prebuilt()
    # 故意问需要连续两步的题，观察 ReAct 的"想→做→再想"
    q = "先算 3 乘 4，再把结果加 10，等于多少？"
    print(f"问：{q}\n")
    result = agent.invoke({"messages": [("user", q)]})

    # 打印完整轨迹：能看到模型怎么一步步推理 + 调工具
    for m in result["messages"]:
        role = type(m).__name__
        tc = getattr(m, "tool_calls", None)
        if tc:
            print(f"[{role}] 调用工具：{[(c['name'], c['args']) for c in tc]}")
        elif m.content:
            print(f"[{role}] {m.content}")


# ----------------------------------------------------------
# 小结：
# - ReAct = Reasoning + Acting：想一步→调工具→看结果→再想，循环到能答。
# - 手搭：agent↔tools 两节点 + 条件边；create_react_agent 一行得到等价 Agent。
# - 何时手搭 vs 用现成：要自定义节点/分支/审批就手搭（Day37/Day39）；
#   标准工具循环直接用它。
# - 面试常问：ReAct 和 Plan-and-Execute 区别？（见 Day33）
# ----------------------------------------------------------
