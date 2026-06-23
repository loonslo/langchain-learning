"""
Day 24 · LangGraph：条件分支 + 循环 + 防死循环
==========================================================
测试工程师转 AI 应用开发

Day23 的图是直线。这节用上 LangGraph 真正的价值：
- 条件分支（conditional_edges）：按 state 当前值决定下一步走哪
- 循环：让某节点回到前面，反复执行，直到满足条件
- recursion_limit：循环最怕"停不下来"。LangGraph 有步数上限，超了就抛错，
  这是工程上必须有的"安全阀"——测试背景的人对这种边界最敏感。

例子：模拟"打磨草稿"，质量不到 3 分就回去重写，最多几轮。
==========================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError


class State(TypedDict):
    quality: int   # 当前质量分
    rounds: int    # 已打磨轮数


def improve(state: State) -> dict:
    """每轮质量 +1，轮数 +1。"""
    q, r = state["quality"] + 1, state["rounds"] + 1
    print(f"  [improve] 第{r}轮，质量 {q}")
    return {"quality": q, "rounds": r}


def route(state: State) -> str:
    """条件函数：返回的字符串决定走哪条边。"""
    return "good_enough" if state["quality"] >= 3 else "keep_going"


def build_app():
    g = StateGraph(State)
    g.add_node("improve", improve)
    g.add_edge(START, "improve")
    # 条件边：route 返回的 key → 目标节点
    g.add_conditional_edges("improve", route, {
        "keep_going": "improve",   # 不达标 → 回到自己，形成循环
        "good_enough": END,        # 达标 → 结束
    })
    return g.compile()


if __name__ == "__main__":
    app = build_app()

    print("===== 正常循环到达标 =====")
    result = app.invoke({"quality": 0, "rounds": 0})
    print("结果：", result)

    print("\n===== 演示防死循环：人为设上限 recursion_limit=2 =====")
    try:
        # 从 0 分到 3 分要 3 轮，但只允许 2 步 → 触发上限保护
        app.invoke({"quality": 0, "rounds": 0}, {"recursion_limit": 2})
    except GraphRecursionError as e:
        print(f"  已被 recursion_limit 拦截（防死循环生效）：{type(e).__name__}")


# ----------------------------------------------------------
# 小结：
# - conditional_edges：用一个"路由函数"按 state 决定下一跳，是分支/循环的核心。
# - 循环 = 把条件边指回前面的节点；靠 route 的退出条件停下来。
# - recursion_limit：步数安全阀，超了抛 GraphRecursionError。生产 Agent 必配，
#   否则模型可能反复调工具停不下来，烧 token。
#
# 动手练习：把退出阈值改成 5，再把 recursion_limit 设成 4，观察被拦截。
# ----------------------------------------------------------
