"""
章节 4.3 合并示例 · 单 Graph 同时体现：分支 + 循环 + 使用工具（通用模板，不依赖 LLM）
===================================================================================
把 章节 4.3 的两个例子（"质量分自循环" 和 "工具 Agent"）合成一个图，
用纯函数模拟，让你在不申请 API Key 的情况下，直接看到三件事如何共存：

  1) 分支：路由函数按 state 决定下一步（去工具 / 结束）
  2) 循环：工具节点执行完回到决策节点，形成"决策→工具→再决策"的循环
  3) 使用工具：专门的 tools 节点执行业务函数，把结果写回 state

通用语义（脱离任何业务）：
  - 决策节点 decide：看 state 里还剩几个待办步骤，决定"调工具处理"还是"收工"
  - 工具节点 run_tool：执行一个"处理步骤"的纯函数，结果累加进 history
  - 路由 route：待办清空 -> done(END)；还有待办 -> use_tool(tools)

运行：python tools/run_chapter.py 4.3 branch_loop_examples.py
（本文件不引入 LLM / API Key，专注把"分支+循环+工具"的控制流跑通）
===================================================================================
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END


# ============================================================
# State：贯穿全程的数据
#   - todo: 剩余待办步骤（列表），空了就结束
#   - history: 已完成的轨迹（工具结果都记这里）
#   - tool_calls: 本图用不上的字段占位说明，这里简化掉，用 todo 长度当"是否还要调工具"
# ============================================================
class TaskState(TypedDict):
    todo: List[str]      # 待办步骤
    history: List[str]   # 已完成步骤的轨迹


# ============================================================
# Node 1：决策节点（decide）—— 读 state，决定走哪条边
#   注意：这里不调 LLM，用 len(todo) 模拟"LLM 判断是否还需要调工具"
# ============================================================
def decide(state: TaskState) -> dict:
    print(f"  [decide] 当前待办：{state['todo']}")
    # 决策节点本身不改业务数据，只打印。真正的"分支"由下方 route() 完成。
    return {}


# ============================================================
# Node 2：工具节点（run_tool）—— 模拟"调用一个工具"
#   真实场景里这里会调用外部 API / 函数；这里用纯函数处理一个待办步骤
# ============================================================
def run_tool(state: TaskState) -> dict:
    todo = state["todo"]
    current = todo[0]                 # 取第一个待办
    result = f"已处理<{current}>"     # 模拟工具执行结果
    print(f"  [tool] 执行工具处理：{current} -> {result}")
    # 工具节点做两件事：把结果记进 history，并把这个待办从 todo 里删掉
    return {
        "history": state["history"] + [result],
        "todo": todo[1:],             # 消费掉一个待办
    }


# ============================================================
# 路由函数：分支判断（这是"分支控制"的核心）
#   返回字符串，由 add_conditional_edges 的映射表决定去哪
# ============================================================
def route(state: TaskState) -> str:
    if len(state["todo"]) == 0:
        return "done"          # 没待办了 -> 结束
    return "use_tool"          # 还有待办 -> 去工具节点


# ============================================================
# 构建单 Graph：
#   START → decide →(条件)→ use_tool(run_tool) → decide → ... 循环
#                              decide →(条件)→ done(END)
# ============================================================
def build_graph():
    g = StateGraph(TaskState)
    g.add_node("decide", decide)
    g.add_node("run_tool", run_tool)

    g.add_edge(START, "decide")
    # 分支：decide 出来后按 route() 决定去向
    g.add_conditional_edges("decide", route, {
        "use_tool": "run_tool",   # 还有待办 -> 调工具
        "done": END,              # 待办清空 -> 结束
    })
    # 循环：工具执行完，回到 decide 重新判断（这就是"决策→工具→再决策"的循环）
    g.add_edge("run_tool", "decide")

    return g.compile()


if __name__ == "__main__":
    print("===== 章节 4.3 合并示例：分支 + 循环 + 使用工具 =====")
    graph = build_graph()
    final = graph.invoke({
        "todo": ["步骤A", "步骤B", "步骤C"],
        "history": [],
    })
    print("\n最终 state：", final)
    print("\n观察：")
    print("  - 分支：decide 每次按 todo 长度决定去工具还是结束")
    print("  - 循环：run_tool 执行完回灌 decide，直到 todo 清空")
    print("  - 工具：run_tool 节点就是'使用工具'，结果写回 history")

    # ----------------------------------------------------------
    # 与 章节 4.3 原文件的对应关系：
    # - 原【一】"质量分自循环" -> 本例的 decide↔run_tool 循环 + route 分支
    # - 原【二】"工具 Agent" -> 本例的 run_tool 节点（ToolNode 的纯函数版）
    # - 原例用 LLM 的 tool_calls 判断，本例用 len(todo) 模拟，控制流完全一致
    # - 真实 Agent 里：decide 换成 LLM 节点，route 换成 tools_condition，
    #   run_tool 换成 ToolNode，其余结构不变——这就是 harness 替你包的循环+分支。
    # ----------------------------------------------------------
