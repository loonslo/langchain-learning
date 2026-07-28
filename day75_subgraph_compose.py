"""
Day 75 · 子图 subgraph 组合：把大图拆成可复用、可独立测的小图
==========================================================
测试工程师转 AI 应用开发  ← 1-33 补充包（Agent 段·补缺口：子图组合）

Agent 图节点一多就难维护：逻辑全堆在一张大图里，想复用一段、单独测一段、
让同事接手一段都难。解法和"把大函数拆小函数"一样——把可复用的一段封装成
【子图 subgraph】，主图把它当一个节点来调。

好处（正好是测试背景的直觉）：
- 复用：同一段（如"检索+校验"）在多个图里共用一份。
- 独立测试：子图能单独 invoke 断言，像给函数写单测。
- 分工：团队各写各的子图，接口对齐即可。

两种组合方式：
【一】父子共享 state 字段：编译后的子图直接 add_node，共享字段自动流动。
【二】父子 state 不同：用一个 wrapper 节点转换输入/输出——子图更解耦、可搬。
    （生产更常用【二】：子图不假设外面的 state 长什么样，自包含才好复用。）

衔接：Day27-39 都是单张图；项目大了（capstone）就靠子图拆分复用与单测。
==========================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ============================================================
# 先做一个"研究小队"子图：topic → notes → summary（纯规则，不调 LLM）
# ============================================================
class ResearchState(TypedDict):
    topic: str
    notes: list
    summary: str


def gather(state: ResearchState) -> dict:
    # 模拟"检索"：针对 topic 收集几条要点
    return {"notes": [f"{state['topic']} 的要点{i}" for i in (1, 2, 3)]}


def summarize(state: ResearchState) -> dict:
    return {"summary": f"【{state['topic']}】" + "；".join(state["notes"])}


def build_research_subgraph():
    g = StateGraph(ResearchState)
    g.add_node("gather", gather)
    g.add_node("summarize", summarize)
    g.add_edge(START, "gather")
    g.add_edge("gather", "summarize")
    g.add_edge("summarize", END)
    return g.compile()   # 编译后就是一个可复用、可单独 invoke 的子图


# ============================================================
# 【子图可独立测试】：像给函数写单测一样，单独喂输入、断言输出
# ============================================================
def demo_subgraph_alone():
    sub = build_research_subgraph()
    out = sub.invoke({"topic": "RAG", "notes": [], "summary": ""})
    print("  子图单独跑 →", out["summary"])
    assert "RAG" in out["summary"] and "；" in out["summary"]   # 可断言 → 可回归
    print("  ✓ 子图可独立断言（这就是拆子图的测试价值，呼应 Day48）")


# ============================================================
# 【一】父子共享 state：编译子图直接当节点
# ============================================================
class SharedParent(TypedDict):
    topic: str          # ↓ 这三个和子图同名，父子共享、自动流动
    notes: list
    summary: str
    report: str         # 父图自己的字段


def make_report(state: SharedParent) -> dict:
    return {"report": f"报告：{state['summary']}（基于 {len(state['notes'])} 条要点）"}


def build_shared_parent():
    g = StateGraph(SharedParent)
    g.add_node("research", build_research_subgraph())   # 子图直接作为一个节点
    g.add_node("report", make_report)
    g.add_edge(START, "research")
    g.add_edge("research", "report")
    g.add_edge("report", END)
    return g.compile()


# ============================================================
# 【二】父子 state 不同：wrapper 节点转换（更解耦，推荐）
# ============================================================
class DiffParent(TypedDict):
    question: str       # 父图字段名和子图完全不同
    answer: str


def research_wrapper(state: DiffParent) -> dict:
    """把父图的 question 翻成子图输入 → 调子图 → 把子图输出翻回父图。
    子图完全不知道外面 state 长啥样，这就是解耦：能原样搬到别的图里复用。"""
    sub = build_research_subgraph()
    sub_out = sub.invoke({"topic": state["question"], "notes": [], "summary": ""})
    return {"answer": sub_out["summary"]}


def build_diff_parent():
    g = StateGraph(DiffParent)
    g.add_node("research", research_wrapper)
    g.add_edge(START, "research")
    g.add_edge("research", END)
    return g.compile()


if __name__ == "__main__":
    print("===== 子图可独立测试 =====")
    demo_subgraph_alone()

    print("\n===== 【一】父子共享 state：子图直接当节点 =====")
    out1 = build_shared_parent().invoke(
        {"topic": "混合检索", "notes": [], "summary": "", "report": ""})
    print("  ", out1["report"])

    print("\n===== 【二】父子 state 不同：wrapper 转换 =====")
    out2 = build_diff_parent().invoke({"question": "Text2SQL 安全", "answer": ""})
    print("  ", out2["answer"])


# ----------------------------------------------------------
# 小结：
# - 子图 = 编译好的图，能被主图当一个节点调，也能单独 invoke 测试。
# - 【一】父子共享字段：add_node(编译子图) 直接用，共享字段自动流动，写着省事。
# - 【二】父子 state 不同：wrapper 节点转换输入输出，子图自包含、可搬、更解耦（推荐）。
# - 价值：复用一段逻辑、独立单测一段、团队分工——和"把大函数拆小函数"一个道理。
#
# 面试话术：
#   "图大了我会拆子图：可复用的一段（比如检索+校验）封装成 subgraph，主图当一个
#    节点调。好处是能复用、能像函数一样独立单测、团队能分工。父子 state 不同时我用
#    wrapper 节点转换，保持子图自包含、可搬——这跟拆小函数、写单测是同一套工程直觉。"
#
# 动手练习：把 Day37 的"搜索+总结"抽成一个子图，让带 HITL 审批的主图复用它，
#          再给这个子图单独写一条 pytest（呼应 Day48 回归）。
# ----------------------------------------------------------
