"""
Day 28 · LangGraph 入门：State / Node / Edge
==========================================================
测试工程师转 AI 应用开发  ← 阶段3 Agent 开篇

前面用 LCEL（| 管道）串链，是"一条直线走到底"。但真实 Agent 要会：
循环（没答好再来一轮）、分支（按情况走不同路）、记状态（中途存中间结果）。
这些 LCEL 干不了，得用图（Graph）。LangGraph 就是"用图描述带状态的流程"。

三个核心概念（先建立体感，今天只搭最简单的线性图）：
1. State：一个共享字典（TypedDict 定义结构），每个节点读它、改它
2. Node：一个函数，输入 state、输出"要更新 state 的部分"
3. Edge：节点之间怎么连；START 是入口，END 是出口

依赖：pip install langgraph
==========================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ---------- 1. 定义 State：整张图共享的数据结构 ----------
class State(TypedDict):
    topic: str        # 输入
    draft: str        # 第一个节点产出
    polished: str     # 第二个节点产出


# ---------- 2. 定义 Node：每个就是普通函数，返回"要更新的字段" ----------
def write_draft(state: State) -> dict:
    print("  [node] write_draft 执行")
    return {"draft": f"关于「{state['topic']}」的初稿。"}


def polish(state: State) -> dict:
    print("  [node] polish 执行")
    return {"polished": state["draft"] + "（已润色）"}


# ---------- 3. 连边：START → write_draft → polish → END ----------
def build_app():
    g = StateGraph(State)
    g.add_node("write_draft", write_draft)
    g.add_node("polish", polish)
    g.add_edge(START, "write_draft")     # 入口
    g.add_edge("write_draft", "polish")  # 顺序流转
    g.add_edge("polish", END)            # 出口
    return g.compile()                   # 编译成可执行的 app


if __name__ == "__main__":
    app = build_app()
    result = app.invoke({"topic": "LangGraph"})
    print("\n最终 state：")
    for k, v in result.items():
        print(f"  {k}: {v}")


# ----------------------------------------------------------
# 小结：
# - LangGraph = 用"图"描述流程；节点改 state，边定顺序，START/END 是出入口。
# - 节点返回的是"要更新的字段"（部分 dict），LangGraph 自动合并进 state。
# - 这张是线性图，和 LCEL 没差别——它的价值要到 Day24（分支/循环）才显出来。
#
# 对比记忆：LCEL 适合固定直链；LangGraph 适合要循环/分支/存状态的 Agent。
#
# 动手练习：加第三个节点 review，在 polished 后面再追加一句评语。
# ----------------------------------------------------------
