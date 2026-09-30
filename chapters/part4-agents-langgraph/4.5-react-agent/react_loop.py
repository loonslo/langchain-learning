"""
章节 4.5 · 在 章节 4.3 合并图上改出 ReAct Agent（不依赖 LLM 的通用模板）
================================================================
章节 4.3 的"决策-工具循环图"已经是 ReAct 的雏形：
    START → decide →(use_tool)→ run_tool → decide → ... →(done)→ END

章节 4.5 用离线模拟展开 ReAct 循环结构，对应关系：
    章节 4.3 的 decide     →  章节 4.5 的 agent    （这里用 len(todo) 模拟"LLM 是否还要调工具"）
    章节 4.3 的 run_tool   →  章节 4.5 的 tools    （执行工具，把结果写回 state）
    章节 4.3 的 route      →  章节 4.5 的 tools_condition（按"有无待办"模拟"有无 tool_calls"）
    章节 4.3 的循环        →  章节 4.5 的 tools→agent 回灌（完全一样的结构）

本文件不引入 LLM / API Key，用纯函数模拟，让你先吃透 ReAct 循环结构。
真实 章节 4.5 只是把 agent 节点换成 "llm_with_tools.invoke(state['messages'])"，
把 tools 节点换成 ToolNode(TOOLS)，把 route 换成 tools_condition。

运行：python tools/run_chapter.py 4.5 react_loop.py（离线）
================================================================
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END


# ============================================================
# State：和 章节 4.3 一样的"待办 + 轨迹"，ReAct 里对应 messages 列表
# ============================================================
class ReactState(TypedDict):
    todo: List[str]      # 待办步骤（模拟 LLM 还没完成的任务）
    history: List[str]   # 工具执行轨迹（模拟 messages 累积）


# ============================================================
# agent 节点（替换 章节 4.3 的 decide）
#   真实 ReAct 里这里是：return {"messages":[llm_with_tools.invoke(state["messages"])]}
#   这里用 len(todo) 模拟"LLM 判断是否还需要调工具"
# ============================================================
def agent(state: ReactState) -> dict:
    print(f"  [agent] 推理中，剩余待办：{state['todo']}")
    return {}   # agent 本身不写业务数据，分支由下方 route 决定


# ============================================================
# tools 节点（替换 章节 4.3 的 run_tool，即 ToolNode 的纯函数版）
#   真实 ReAct 里这里是 ToolNode(TOOLS)，自动执行模型要求的工具
# ============================================================
def tools(state: ReactState) -> dict:
    current = state["todo"][0]
    result = f"工具执行结果<{current}>"
    print(f"  [tools] 执行工具：{current} -> {result}")
    return {
        "history": state["history"] + [result],
        "todo": state["todo"][1:],   # 消费掉一个待办（模拟"工具结果回灌后任务推进"）
    }


# ============================================================
# 路由（对应 章节 4.3 的 route，真实 ReAct 里是 tools_condition）
#   真实：有 tool_calls -> "call_tool"，否则 -> END
#   这里：还有待办 -> "call_tool"，否则 -> END
# ============================================================
def router(state: ReactState) -> str:
    return "call_tool" if len(state["todo"]) > 0 else END


# ============================================================
# 构建图：结构 = 章节 4.3 合并图，节点名换成 agent/tools
#   START → agent →(call_tool)→ tools → agent → ... →(END)→ END
# ============================================================
def build_react():
    g = StateGraph(ReactState)
    g.add_node("agent", agent)
    g.add_node("tools", tools)
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", router, {
        "call_tool": "tools",   # 还要干 -> 调工具
        END: END,               # 干完了 -> 结束
    })
    g.add_edge("tools", "agent")   # 工具结果回灌 agent，再想一轮（循环 = ReAct 核心）
    return g.compile()


if __name__ == "__main__":
    print("===== 章节 4.5 从 章节 4.3 改出 ReAct（无 LLM 版）=====")
    app = build_react()
    final = app.invoke({"todo": ["步骤A", "步骤B", "步骤C"], "history": []})
    print("\n最终 state：", final)
    print("\n看出来了吧？这图和 章节 4.3 合并图是同一个骨架：")
    print("  章节 4.3: START→decide→(use_tool)→run_tool→decide→...→(done)→END")
    print("  章节 4.5: START→agent →(call_tool)→tools →agent →...→(END)→END")
    print("  区别只在：decide/run_tool 换成 agent/tools，且真实版由 LLM 的 tool_calls 驱动。")

    # ----------------------------------------------------------
    # 对照真实 章节 4.5 手搭版（仅节点实现不同，图结构完全一致）：
    #
    #   def agent(state):  # 真实
    #       return {"messages": [llm_with_tools.invoke(state["messages"])]}
    #   g.add_node("tools", ToolNode(TOOLS))      # 真实 ToolNode
    #   g.add_conditional_edges("agent", tools_condition)   # 真实按 tool_calls 判断
    #   g.add_edge("tools", "agent")
    # ----------------------------------------------------------
