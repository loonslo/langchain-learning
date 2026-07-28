"""
Day 27 · LangGraph 入门（上）：State / Node / Edge，先搭最小线性图
==========================================================
测试工程师转 AI 应用开发  ← 阶段3 Agent 开篇（拆自原 Day28 上半）

前面用 LCEL（| 管道）串链，是"一条直线走到底"。但真实 Agent 要会：
循环（没答好再来一轮）、分支（按情况走不同路）、记状态（中途存中间结果）。
这些 LCEL 干不了，得用图（Graph）。LangGraph 就是"用图描述带状态的流程"。

今天只搭最简单的【线性图】，把三个基本件认清、建立体感：
- State：一份贯穿全程的数据（用 TypedDict 声明有哪些字段）。
- Node：一个函数，读 state、返回"要更新的字段"（部分 dict），LangGraph 自动合并回 state。
- Edge：连接节点、定义顺序；START 是入口、END 是出口。

注意：线性图（今天）和 LCEL 其实没差别——图的价值要到"分支/循环/状态"才显出来，
那是 Day28 的事。今天先把最小骨架跑通，不引入 LLM，专注理解"图怎么动"。

衔接：Day28 在此基础上加分支与循环（conditional_edges）+ 对比手写循环；
      Day30 再加工具调用做成 ReAct Agent。
==========================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ============================================================
# State：声明这张图从头到尾要传递哪些字段
# ============================================================
class DraftState(TypedDict):
    topic: str        # 输入
    draft: str        # 第一个节点产出
    polished: str     # 第二个节点产出


# ============================================================
# Node：每个节点是一个函数，读 state、返回"要更新的字段"
# ============================================================
def write_draft(state: DraftState) -> dict:
    print("  [node] write_draft 执行")
    # 只返回自己负责的字段，LangGraph 会把它合并进整份 state
    return {"draft": f"关于「{state['topic']}」的初稿。"}


def polish(state: DraftState) -> dict:
    print("  [node] polish 执行")
    return {"polished": state["draft"] + "（已润色）"}


# ============================================================
# Edge：把节点按顺序连起来，START→…→END
# ============================================================
def build_linear():
    g = StateGraph(DraftState)
    g.add_node("write_draft", write_draft)
    g.add_node("polish", polish)
    g.add_edge(START, "write_draft")        # 入口 → 第一个节点
    g.add_edge("write_draft", "polish")     # 顺序执行
    g.add_edge("polish", END)               # 最后一个节点 → 出口
    return g.compile()


if __name__ == "__main__":
    print("===== 最小线性图：State / Node / Edge =====")
    linear = build_linear()
    # invoke 传入初始 state（只需给输入字段），跑完返回最终完整 state
    final = linear.invoke({"topic": "LangGraph"})
    print("最终 state：", final)


# ----------------------------------------------------------
# 小结：
# - LangGraph = 用"图"描述流程：节点改 state，边定顺序，START/END 是出入口。
# - 节点只返回"要更新的字段"（部分 dict），LangGraph 自动合并进整份 state
#   （合并规则叫 reducer，默认覆盖；详见 Day29）。
# - 线性图和 LCEL 没本质差别——图的价值在"分支/循环/状态"，那是 Day28。
# - 建体感三问：这张图有哪些字段(State)？每步改了什么(Node)？走的什么顺序(Edge)？
#
# 面试话术：
#   "LangGraph 把流程建模成状态图：State 是贯穿全程的数据，Node 读写 State，
#    Edge 定顺序。线性场景它等价于 LCEL，真正价值在能表达分支、循环和持久化状态。"
#
# 动手练习：给这张图再加一个 review 节点（polish→review→END），
#          在 state 里加一个 review 字段，跑通并观察最终 state 多了什么。
# ----------------------------------------------------------
