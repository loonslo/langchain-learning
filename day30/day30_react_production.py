"""
Day 30 · 生产级 ReAct Agent（自定义 State 版）：把 Day28 教学骨架换成真实 LLM + 工具
================================================================
为什么不用 MessagesState？
    初学者看 MessagesState 只看到一个 messages 列表，看不出"每一步 state 怎么变"。
    这里用自定义 TypedDict，把 state 拆成几个字段，每走一个节点都打印它改了什么，
    你就能清楚看到：agent 往 messages 里加了什么、tools 回灌了什么。

这张图里的每个概念，对应生产里的真实实现：

    Day28 教学版              生产级对应（本文件）
    ───────────────────────────────────────────────
    TaskState                 ReactState（自定义 TypedDict）
    todo / history            messages（LLM 看到的完整对话+工具轨迹）
    decide 节点               agent 节点：llm_with_tools.invoke(messages)
    run_tool 节点              tools 节点：ToolNode([...])
    route() 硬编码             tools_condition（按 LLM 的 tool_calls 动态分支）
    循环：run_tool→decide       循环：tools→agent（结果回灌 messages）

运行：
    .venv\Scripts\python.exe day30_react_production.py
================================================================
"""

import os
from typing import TypedDict, Annotated, Sequence
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 自定义 State：显式拆字段，让"怎么走"一目了然
# ============================================================
# messages 用 Annotated[Sequence[BaseMessage], operator.add]：
#   - Sequence[BaseMessage] 是类型（消息列表）
#   - operator.add 是 reducer：多个节点都写 messages 时，框架把各自的增量"追加"，
#     而不是互相覆盖。这样 agent 加一条、tools 加一条，全部保留在 state 里。
class ReactState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    step: Annotated[list[str], operator.add]   # 记录走了哪些节点，便于复盘
    finished: bool                             # 模型是否已决定最终回答


# ============================================================
# 生产 LLM：绑定工具，让模型自己决定调不调
# ============================================================
def get_llm(temperature: float = 0.0, model: str = "deepseek-chat", **kwargs):
    """DeepSeek 对话模型（OpenAI 兼容）。"""
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temperature,
        **kwargs,
    )


# ============================================================
# 教学工具：对应 Day28 的 run_tool 节点
# 极简，不联网、不需要 API key，纯粹用来演示"模型会调工具 + 会循环"。
# 内部就是一个确定性字典查询——返回的是真实映射结果，不是编的天气。
# ============================================================
_WEATHER_DB = {
    "北京": "晴，25℃",
    "上海": "多云，28℃",
    "广州": "雷阵雨，30℃",
    "深圳": "阴，29℃",
}


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。city 如 '北京' / '上海' / '广州' / '深圳'。"""
    if city not in _WEATHER_DB:
        return f"暂无 {city} 的天气数据"
    return f"{city}：{_WEATHER_DB[city]}"


TOOLS = [get_weather]
TOOL_MAP = {t.name: t for t in TOOLS}


# ============================================================
# 生产级 ReAct 图（自定义 State 手搭版，对应 Day28 build_graph）
# ============================================================
# llm_with_tools：模块级常量，绑定了工具。agent 节点直接引用它，
# 这样 agent 定义在顶层也能拿到 LLM，不需要闭包捕获。
llm_with_tools = get_llm(temperature=0).bind_tools(TOOLS)


def agent(state: ReactState) -> dict:
    """对应 Day28 的 decide 节点：让 LLM 根据当前 messages 决定下一步。"""
    print(f"\n[agent] 进入：当前已有 {len(state['messages'])} 条消息")
    response: AIMessage = llm_with_tools.invoke(state["messages"])
    # 关键：agent 只往 messages 里追加一条 AIMessage（可能带 tool_calls）
    return {
        "messages": [response],
        "step": ["agent"],
        "finished": len(response.tool_calls) == 0,  # 没有 tool_calls = 已决定回答
    }


def tools(state: ReactState) -> dict:
    """对应 Day28 的 run_tool 节点：执行模型选中的工具，把结果回灌 messages。"""
    last_ai = state["messages"][-1]
    print(f"[tools] 进入：执行 {len(last_ai.tool_calls)} 个工具调用")
    tool_messages = []
    for call in last_ai.tool_calls:
        name = call["name"]
        args = call["args"]
        print(f"         → 调 {name}({args})")
        result = TOOL_MAP[name].invoke(args)
        tool_messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
    # 关键：tools 只往 messages 里追加 ToolMessage（结果回灌）
    return {"messages": tool_messages, "step": ["tools"]}


def build_react_agent():
    """
    图结构完全对应 Day28：
        START → agent →(tools_condition)→ tools → agent → ... →(END)→ END

    注意：这里不用 create_react_agent 现成件，而是手搭，
    这样你能看清每个节点里到底对 state 做了什么。
    节点函数（agent/tools）在模块顶层定义，和 day31~day39 风格统一，可复用、可单测。
    """
    g = StateGraph(ReactState)
    g.add_node("agent", agent)        # decide 的真实版
    g.add_node("tools", tools)        # run_tool 的真实版

    g.add_edge(START, "agent")

    # route() 的真实版：tools_condition 按"最后一条 AIMessage 有无 tool_calls"分支
    #   有 tool_calls -> "tools"
    #   没有         -> END
    g.add_conditional_edges("agent", tools_condition)

    # 循环：工具执行完，结果回灌 agent，让 LLM 再决策一轮
    g.add_edge("tools", "agent")

    return g.compile()


# ============================================================
# 运行 + 可视化轨迹
# ============================================================
def run_agent(question: str):
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("请先设置 DEEPSEEK_API_KEY 环境变量。")
        return

    app = build_react_agent()
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "step": [],
        "finished": False,
    }

    print(f"===== 问题：{question} =====")
    print("--- 初始 state: messages 只有 1 条(HumanMessage) ---")

    for chunk in app.stream(initial_state, stream_mode="updates"):
        # stream_mode="updates"：每次只返回"刚执行的节点改了哪些字段"
        for node, update in chunk.items():
            added = update.get("messages", [])
            kinds = [type(m).__name__ for m in added]
            print(f"  ▼ 节点 [{node}] 执行完，往 state 追加了: {kinds}")

    # 拿最终完整 state（再 invoke 一次拿返回值，或直接用上面 accumulate）
    final = app.invoke(initial_state)
    print("\n--- 最终 state ---")
    print(f"  finished = {final['finished']}")
    print(f"  step 轨迹 = {final['step']}")
    print(f"  messages 共 {len(final['messages'])} 条：")
    for i, m in enumerate(final["messages"], 1):
        head = m.content[:60] + ("..." if len(m.content) > 60 else "")
        calls = f"  tool_calls={m.tool_calls}" if getattr(m, "tool_calls", None) else ""
        print(f"    {i}. {type(m).__name__}: {head}{calls}")


if __name__ == "__main__":
    # 示例 1：需要天气信息 → 触发 get_weather 一次
    run_agent("北京现在适合穿短袖吗？")
    print("\n" + "=" * 70 + "\n")
    # 示例 2：多城市 → 模型可能多次调用同一个工具（体现循环，不用第二个工具）
    run_agent("北京和上海，哪个更热？")


# ----------------------------------------------------------
# 与 Day28 教学骨架的一一对应：
#
#   Day28                     本文件（自定义 State）
#   ───────────────────────────────────────────────────────
#   TaskState(todo, history)  ReactState(messages, step, finished)
#   todo: List[str]           messages 里累积的 AIMessage/ToolMessage
#   history: List[str]        messages（完整对话+工具轨迹）
#   decide(state)             agent(state) { llm_with_tools.invoke(messages) }
#   run_tool(state)           tools(state) { 执行 tool_calls → ToolMessage }
#   route(state) -> str       tools_condition -> "tools" | END
#   add_edge("run_tool","decide")  add_edge("tools", "agent")
#
# 为什么这样更清楚：
#   - state 字段拆开，每步打印"往 messages 追加了什么"，你能看到 ReAct 循环
#   - "下一步"仍由 LLM 自己拍板（看 tool_calls 是否为空），不是代码写死
# ----------------------------------------------------------
