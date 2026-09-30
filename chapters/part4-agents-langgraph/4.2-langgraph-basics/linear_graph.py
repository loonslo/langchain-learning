"""
章节 4.2 · 单 Graph 最小线性控制（通用模板）
==========================================
严格对齐 graph_basics.py 的节奏：只搭最小线性图，
只讲三件套：State / Node / Edge，只用一个线性控制（写死的顺序）。

通用语义（脱离任何业务）：
  - State：贯穿全程的数据，这里用 history 记录流程轨迹。
  - Node：step_a / step_b，每个节点读 state、返回要更新的字段。
  - Edge：START -> step_a -> step_b -> END，顺序写死（线性控制）。

注意：本文件没有任何分支、没有任何循环、不引入 LLM，
      专注理解"线性控制下，图怎么一步步动"。分支/循环是后面（4.3）的事。

运行：python tools/run_chapter.py 4.2 linear_graph.py（离线）
==========================================
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END


# ============================================================
# State：声明这张图从头到尾要传递哪些字段
# ============================================================
class FlowState(TypedDict):
    history: List[str]   # 流程轨迹，每个节点往里追加一步


# ============================================================
# Node：每个节点是一个函数，读 state、返回"要更新的字段"
# ============================================================
def step_a(state: FlowState) -> dict:
    print("  [node] step_a 执行")
    return {"history": state["history"] + ["step_a 完成"]}


def step_b(state: FlowState) -> dict:
    print("  [node] step_b 执行")
    return {"history": state["history"] + ["step_b 完成"]}


# ============================================================
# Edge：把节点按固定顺序连起来，START -> step_a -> step_b -> END（线性控制）
# ============================================================
def build_linear():
    g = StateGraph(FlowState)
    g.add_node("step_a", step_a)
    g.add_node("step_b", step_b)
    g.add_edge(START, "step_a")        # 入口 -> 第一个节点
    g.add_edge("step_a", "step_b")     # 顺序执行
    g.add_edge("step_b", END)          # 最后一个节点 -> 出口
    return g.compile()


if __name__ == "__main__":
    print("===== 最小线性图：State / Node / Edge（线性控制）=====")
    linear = build_linear()
    final = linear.invoke({"history": []})
    print("最终 state：", final)

    # ----------------------------------------------------------
    # 小结：
    # - 线性控制 = 用 add_edge 把节点顺序写死，等价于 LCEL 的 step_a | step_b。
    # - 节点只返回"要更新的字段"（部分 dict），LangGraph 自动合并进整份 state。
    # - 建体感三问：这张图有哪些字段(State)？每步改了什么(Node)？走的什么顺序(Edge)？
    # - 图的价值（分支/循环/状态持久化）在后面才显现；本节先把"线性控制"跑通。
    # ----------------------------------------------------------
