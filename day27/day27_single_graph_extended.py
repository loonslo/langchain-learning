"""
Day27 扩充 · 单 Graph 核心能力（通用模板：线性 / 分支 / 循环）
============================================================
把"写稿→润色→审核"这种具体业务，换成完全通用的学习示例，
目标是让你抽象出 LangGraph 的通用骨架，而不是记住某个业务。

通用语义：
  - State 里只有一个 process 字段（当前流程说明）和几个控制字段。
  - step_a / step_b / step_c 是三个"通用处理步骤"，谁也不假设自己在做什么业务。
  - 每个节点只做一件事：把 state 往前推一步，并（可选）写一条轨迹到 history。
  - 分支：step_c 校验结果，决定是否 "retry"（回 step_b）还是 "done"（结束）。
  - 循环：靠 attempts 计数防止死循环。

运行：.venv\Scripts\python.exe day27_single_graph_extended.py
============================================================
"""

from typing import TypedDict, Literal, List
from langgraph.graph import StateGraph, START, END


# ============================================================
# 通用 State：任何"带状态的流程"都长这样
#   - history: 每一步留下的轨迹（用自定义 reducer 累加，见下方 Annotated）
#   - attempts: 循环计数，防止死循环
#   - approved: 校验是否通过（分支判断依据）
# ============================================================
# 注：这里用 list 直接演示"累加字段"。Day29 才会正式讲 Annotated + reducer，
#     现在只需知道：返回 {"history": [...]} 时，框架把新列表"接在"旧列表后面。
#     为简单起见，本例在节点里手动 append（教学用，不破坏可运行性）。
class FlowState(TypedDict):
    history: List[str]      # 流程轨迹
    attempts: int           # 已尝试次数
    approved: bool          # 校验是否通过


# ============================================================
# 通用节点：每个节点 = "把流程往前推一步"
#   约定：节点读 state，返回要更新的字段（部分 dict）
# ============================================================
def step_a(state: FlowState) -> dict:
    print("  [node] step_a 执行")
    h = state["history"] + ["step_a 完成"]
    return {"history": h}


def step_b(state: FlowState) -> dict:
    print("  [node] step_b 执行")
    h = state["history"] + ["step_b 完成"]
    return {"history": h, "attempts": state["attempts"] + 1}


def step_c(state: FlowState) -> dict:
    print("  [node] step_c 执行（校验点）")
    # 通用校验规则：attempts >= 2 视为通过；否则打回重做
    ok = state["attempts"] >= 2
    h = state["history"] + [f"step_c 校验：{'通过' if ok else '不通过'}"]

    # 关键观察：返回里同时更新 history 和 approved 两个字段
    # —— 一个节点可以写多个字段，它们各自按 reducer 合并回 state
    return {"history": h, "approved": ok}


# ============================================================
# 通用分支路由：根据 approved 决定下一步
# ============================================================
def route_after_check(state: FlowState) -> Literal["retry", "done"]:
    # 返回的是"语义名"，由下方映射绑定到真实节点 / END
    return "done" if state["approved"] else "retry"


# ============================================================
# 构建单 Graph（通用结构）
#   START → step_a → step_b → step_c
#                 ↑______(不通过)______|
#        step_c --(通过)--> END
# ============================================================
def build_graph():
    g = StateGraph(FlowState)

    g.add_node("step_a", step_a)
    g.add_node("step_b", step_b)
    g.add_node("step_c", step_c)

    # 1) 线性主干
    g.add_edge(START, "step_a")
    g.add_edge("step_a", "step_b")
    g.add_edge("step_b", "step_c")

    # 2) 条件分支：校验通过则结束，否则回到 step_b 重做
    g.add_conditional_edges(
        "step_c",
        route_after_check,
        {
            "retry": "step_b",   # 不通过 -> 回 step_b 再来一轮（这就是"循环"）
            "done": END,         # 通过 -> 结束
        },
    )

    return g.compile()


if __name__ == "__main__":
    print("===== 单 Graph 通用模板：线性 + 分支 + 循环 =====")
    graph = build_graph()

    final = graph.invoke({
        "history": [],
        "attempts": 0,
        "approved": False,
    })

    print("\n最终 state：", final)
    print("\n观察：")
    print(f"  - 流程轨迹：{final['history']}")
    print(f"  - 共循环了 {final['attempts']} 次才通过校验")
    print(f"  - 这就是「图循环」：条件边指回上游节点，而非新写代码")

    # ----------------------------------------------------------
    # 通用结论（脱离任何业务都能记住）：
    # - 单 Graph = 一份 State + 若干 Node + 若干 Edge。
    # - 节点职责单一：读 state，返回"要更新的字段"（可一次更新多个）。
    # - 分支：add_conditional_edges(源节点, 路由函数, {返回名: 目标})
    #        路由函数返回字符串，由映射表决定去哪个节点或 END。
    # - 循环：让分支边指回上游节点；务必用 attempts/rounds 之类计数器防死循环。
    # - 任何业务（写稿、客服、代码生成…）都是这套骨架套上不同节点函数。
    # ----------------------------------------------------------
