"""
Day 36 · streaming 流式中间步骤 + human-in-the-loop 人工确认
==========================================================
测试工程师转 AI 应用开发  ★安全，面试/上线及格线★

这天两件事：
1. streaming：长任务让用户干等体验差。app.stream() 能边执行边吐出每一步
   （走到哪个节点、state 怎么变），既改善体验也方便观测 Agent 在干什么。
2. HITL：删数据、发邮件、付款这类高风险动作绝不能让模型自己拍板。
   执行前用 interrupt() 把图暂停、把动作抛给人，确认了才继续，否则取消。

HITL 两道防线：interrupt 等人审批（靠 checkpointer 暂停-恢复）+ 危险工具只模拟。
==========================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command


class State(TypedDict):
    target: str       # 要操作的对象，比如某个文件
    result: str


def prepare(state: State) -> dict:
    print(f"  [prepare] 准备删除：{state['target']}")
    return {}


def confirm(state: State) -> dict:
    """高风险动作前暂停，把动作抛给人确认。interrupt 会让图停在这里。"""
    decision = interrupt({
        "action": "delete",
        "target": state["target"],
        "ask": "确认删除吗？回复 yes / no",
    })
    # 人 resume 后，decision 就是人给的值
    if str(decision).lower() == "yes":
        # 安全：这里只模拟，绝不调真实删除
        return {"result": f"（已模拟删除 {state['target']}）"}
    return {"result": "用户取消，未执行"}


def build_app():
    g = StateGraph(State)
    g.add_node("prepare", prepare)
    g.add_node("confirm", confirm)
    g.add_edge(START, "prepare")
    g.add_edge("prepare", "confirm")
    g.add_edge("confirm", END)
    # HITL 必须有 checkpointer：图要能"暂停存档、再恢复"
    return g.compile(checkpointer=InMemorySaver())


def demo_streaming():
    """流式吐出图的每一步：stream_mode='updates' 返回每个节点的增量更新。
    跑到 interrupt 节点会停下，正好能看到"哪一步要等人"。"""
    app = build_app()
    cfg = {"configurable": {"thread_id": "stream-demo"}}
    print("流式中间步骤（每到一个节点就吐一次）：")
    for step in app.stream({"target": "old_logs.txt", "result": ""}, cfg):
        print("  ->", step)


if __name__ == "__main__":
    print("===== 1) streaming 中间步骤 =====")
    demo_streaming()

    print("\n===== 2) HITL 人工审批 =====")
    app = build_app()
    cfg = {"configurable": {"thread_id": "task-1"}}

    # 第一次 invoke：跑到 interrupt 就停下，返回里带 __interrupt__
    out = app.invoke({"target": "report.docx", "result": ""}, cfg)
    pause = out["__interrupt__"][0].value
    print(f"\n图已暂停，等待人工确认：{pause}")

    # 模拟人工批准：用 Command(resume=...) 把决定传回去，图从断点继续
    print("\n人工回复 yes，继续执行：")
    final = app.invoke(Command(resume="yes"), cfg)
    print("  结果：", final["result"])

    # 另一个会话演示拒绝
    cfg2 = {"configurable": {"thread_id": "task-2"}}
    app.invoke({"target": "db_backup.sql", "result": ""}, cfg2)
    final2 = app.invoke(Command(resume="no"), cfg2)
    print("\n另一会话人工回复 no：", final2["result"])


# ----------------------------------------------------------
# 小结：
# - interrupt() 在高风险节点把图暂停，把动作抛给人；Command(resume=值) 恢复执行。
# - HITL 依赖 checkpointer（要能暂停存档再恢复），所以 compile 必须传 checkpointer。
# - 工具安全：危险工具只模拟，绝不接真实删除/发送/支付权限——这是上线红线。
#
# 面试话术：
#   "Agent 的高风险动作我都加 human-in-the-loop：interrupt 暂停等人工审批，
#    且危险工具不给真实权限，只做模拟——宁可拦错，不可误删。"
#
# 动手练习：把 confirm 改成"只有金额 > 1000 才 interrupt，否则直接放行"。
# ----------------------------------------------------------
