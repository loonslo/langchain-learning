"""
Day 29 · State 设计与 reducer：节点返回怎么"合"进 state（并发写入不丢）
==========================================================
测试工程师转 AI 应用开发  ← 补生产缺口#1（承接 Day28 基础，垫 Day39 fan-out）

Day28 你会搭图了，但漏了一件生产必踩的事：
「节点 return 一个 dict，这个 dict 怎么并进整张图的 state？」

默认规则是【覆盖】：节点返回 {"x": 新值} → state["x"] 直接被新值替换。
单线程线性图没问题；可一旦【累加】或【并发】就出事：
  - 累加：想把每步结果 append 进列表，覆盖会把前面的冲掉；
  - fan-out（多节点同一 step 写同一字段）：没 reducer 框架直接报错（InvalidUpdateError）；
    若是手拼 state['x']+[...]（如 Day39），真并发下则是静默丢数据。

解法：给字段声明一个 reducer（合并函数）。用 Annotated[类型, reducer]。
LangGraph 每次拿"旧值 + 节点新返回值"喂给 reducer，得到合并后的新值。
  - 不写 reducer  → 默认覆盖（last write wins）
  - operator.add  → 列表拼接 / 数字相加
  - add_messages  → 消息专用合并（这就是 MessagesState 背后的东西！）
  - 自定义函数    → 你想怎么合就怎么合

衔接：Day30 ReAct 的 MessagesState 就是 add_messages 的封装；
      Day39 fan-out 的并发写入，正确姿势就是本节的 operator.add。
==========================================================
"""

from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.errors import InvalidUpdateError
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage


# ============================================================
# 【一】默认"覆盖" vs reducer"累加"——一眼看清区别
# ============================================================
class OverwriteState(TypedDict):
    log: list          # 不加 reducer → 默认覆盖


class AccumulateState(TypedDict):
    log: Annotated[list, operator.add]   # 加 reducer → 每次返回都拼接，不丢


def step_a(state) -> dict:
    return {"log": ["A 干了活"]}


def step_b(state) -> dict:
    return {"log": ["B 干了活"]}


def build(state_schema):
    g = StateGraph(state_schema)
    g.add_node("a", step_a)
    g.add_node("b", step_b)
    g.add_edge(START, "a")
    g.add_edge("a", "b")
    g.add_edge("b", END)
    return g.compile()


def demo_overwrite_vs_accumulate():
    print("默认覆盖（OverwriteState）：B 的返回把 A 冲掉")
    out1 = build(OverwriteState).invoke({"log": []})
    print("  最终 log =", out1["log"], "  ← A 的记录没了")

    print("加 operator.add（AccumulateState）：A、B 都留下")
    out2 = build(AccumulateState).invoke({"log": []})
    print("  最终 log =", out2["log"], "  ← 两步都在")


# ============================================================
# 【二】fan-out 写同一字段：没 reducer 框架直接报错（强制用 reducer）
# ============================================================
# 关键事实：普通 fan-out（多条边从 START 出发）里，def/pro/case 三个节点在
# 【同一个 step】被调度，它们都会写 results 字段。若该字段没有 reducer，
# 框架合并写入时会直接抛 InvalidUpdateError——"一个 step 内同一字段只能收到一个值，
# 要用 Annotated 处理多个值"。也就是说：fan-out 多节点写同一字段，reducer 不是
# "建议"而是"强制"，不然图根本跑不起来（这不是静默覆盖，是硬报错）。
# （results 只是自己起的字段名，不是保留字，叫 notes/angles 都行）

class FanStateNoReducer(TypedDict):
    # 没写 reducer → 默认覆盖：三个分支谁最后写谁留下，前两条被冲掉
    results: list


class FanState(TypedDict):
    # 写了 reducer → 三次返回拼接，三条都在
    results: Annotated[list, operator.add]


def branch_def(state) -> dict:
    return {"results": ["定义：它是什么"]}


def branch_pro(state) -> dict:
    return {"results": ["优缺点：可控但需规划"]}


def branch_case(state) -> dict:
    return {"results": ["例子：搭个带审批的搜索 Agent"]}


def build_fanout(state_schema):
    g = StateGraph(state_schema)
    g.add_node("def", branch_def)
    g.add_node("pro", branch_pro)
    g.add_node("case", branch_case)
    g.add_node("merge", lambda s: {})   # 汇聚点：只收口，对比结果在 demo 里看
    for n in ["def", "pro", "case"]:
        g.add_edge(START, n)     # fan-out：三个分支都从 START 出发
        g.add_edge(n, "merge")   # fan-in：汇聚到 merge
    g.add_edge("merge", END)
    return g.compile()


def demo_fanout():
    print("没 reducer：fan-out 三分支写同一 results → 框架直接报错（强制用 reducer）")
    try:
        build_fanout(FanStateNoReducer).invoke({"results": []})
        print("  （意外：居然没报错）")
    except InvalidUpdateError as e:
        print("  InvalidUpdateError：", str(e).split(". ")[0])

    print("加 operator.add（reducer）：框架合并三次写入，三条都留")
    out_good = build_fanout(FanState).invoke({"results": []})
    print("  最终 results 共", len(out_good["results"]), "条 →", out_good["results"])
    # 衔接 Day39：那里用 state['angles']+[...] 手拼，在真并发下会丢，这里交给 reducer 才安全


# ============================================================
# 【二·补】想要有序？reducer 只管"不丢"，顺序自己用序号约定
# ============================================================
# 上一节证明：fan-out 同 step 多节点并行，谁先完成谁先被 add 进列表，顺序未定义。
# reducer（operator.add）保证"三条都不丢"，但不管顺序。要可复现的顺序，做法就是：
# 让每个分支在产出里带一个序号，最后按序号排序——顺序与"谁先跑完"彻底解耦。
class OrderedFanState(TypedDict):
    results: Annotated[list, operator.add]   # 照样拼接，但每项是个 (序号, 文本) 元组


def branch_def_o(state) -> dict:
    return {"results": [(0, "定义：它是什么")]}


def branch_pro_o(state) -> dict:
    return {"results": [(1, "优缺点：可控但需规划")]}


def branch_case_o(state) -> dict:
    return {"results": [(2, "例子：搭个带审批的搜索 Agent")]}


def merge_o(state) -> dict:
    ordered = [text for _, text in sorted(state["results"])]   # 按序号排
    print("  [merge] 按序号排好：", ordered)
    return {}   # 不写回 results，否则会被 reducer 追加成两份


def build_fanout_ordered():
    g = StateGraph(OrderedFanState)
    g.add_node("def", branch_def_o)
    g.add_node("pro", branch_pro_o)
    g.add_node("case", branch_case_o)
    g.add_node("merge", merge_o)
    for n in ["def", "pro", "case"]:
        g.add_edge(START, n)
        g.add_edge(n, "merge")
    g.add_edge("merge", END)
    return g.compile()


def demo_fanout_ordered():
    print("带序号 + 消费端排序：顺序稳定可复现（不管分支谁先完成）")
    out = build_fanout_ordered().invoke({"results": []})
    ordered = [text for _, text in sorted(out["results"])]
    print("  有序 results =", ordered)


# ============================================================
# 【三】add_messages：MessagesState 的真身 + 自定义 reducer
# ============================================================
class ChatState(TypedDict):
    # 这个 ChatState 和框架预定义的 MessagesState 完全等价——MessagesState 的"全部"
    # 就只有 messages 这一个字段（Annotated[list, add_messages]）。想加别的字段（如
    # results）就自己写 TypedDict，比用 MessagesState 更灵活。
    # add_messages 会按消息 id 智能合并（去重/更新），所以多轮消息自动累积。
    messages: Annotated[list, add_messages]




def demo_add_messages():
    # 直接调用 reducer 看它怎么合：旧消息 + 新消息 → 追加
    old = [HumanMessage(content="你好", id="1")]
    new = [AIMessage(content="你好，我是助手", id="2")]
    merged = add_messages(old, new)
    print("add_messages 合并：", [(type(m).__name__, m.content) for m in merged])
    print("MessagesState 里的 messages 字段，用的就是这个 reducer（所以多轮消息会自动累积）")


def keep_last_n(existing: list, new: list, n: int = 4) -> list:
    """自定义 reducer：合并后只保留最近 n 条（天然防上下文爆窗，呼应 Day35 压缩）。"""
    return (existing + new)[-n:]


class WindowState(TypedDict):
    # 自定义 reducer 要带参数时用 lambda 包一层：lambda 的两个参数(旧值, 新值)是
    # 框架固定传入的，内部把"保留几条"(4) 当配置焊死，调用 keep_last_n。
    messages: Annotated[list, lambda existing, new: keep_last_n(existing, new, 4)]


def demo_custom_reducer():
    g = StateGraph(WindowState)
    g.add_node("push", lambda s: {"messages": ["新一条"]})
    g.add_edge(START, "push")
    g.add_edge("push", END)
    app = g.compile()
    state = {"messages": ["1", "2", "3", "4"]}
    out = app.invoke(state)
    print("自定义 reducer（只留最近 4 条）：", out["messages"], " ← 最老的被挤掉")


if __name__ == "__main__":
    print("===== 【一】默认覆盖 vs reducer 累加 =====")
    demo_overwrite_vs_accumulate()
    print("\n===== 【二】fan-out 写同一字段：无 reducer 直接报错，必须用 reducer =====")
    demo_fanout()
    print("\n===== 【二·补】想要有序：带序号 + 消费端排序 =====")
    demo_fanout_ordered()
    print("\n===== 【三】add_messages = MessagesState 的真身 =====")
    demo_add_messages()
    print("\n===== 【三·补】自定义 reducer：滑动窗口 =====")
    demo_custom_reducer()


# ----------------------------------------------------------
# 小结：
# - 节点返回的 dict 怎么并入 state，由字段的 reducer 决定：不写=覆盖，写了=按函数合并。
# - Annotated[类型, reducer] 是声明方式；operator.add 拼接、add_messages 合消息、自定义随你。
# - 多个节点在同一 step 写同一字段（fan-out），该字段必须有 reducer（如 operator.add），
#   否则框架直接抛 InvalidUpdateError——这不是"静默覆盖丢数据"，而是"图都跑不起来"。
# - reducer 只保证"不丢"，不保证"有序"（并发完成顺序未定义）；要稳定顺序，
#   让产出带序号、最后按序号排序即可（见【二·补】），顺序与"谁先跑完"解耦。
# - MessagesState 不是魔法，就是 {"messages": Annotated[list, add_messages]}。
#
# 面试话术：
#   "并发节点写同一状态字段，我不会手动拼列表——那在真并发下会丢更新；
#    我给字段声明 reducer（operator.add / add_messages），让框架保证合并的正确性。"
#
# 动手练习：给 Day39 的 fan-out 把 angles 改成 Annotated[list, operator.add]，
#          去掉手拼的 state['angles']+[...]，验证并发下不再丢数据。
# ----------------------------------------------------------
