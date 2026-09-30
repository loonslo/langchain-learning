"""
章节 4.1 · Agent 模式：先决定控制权放在哪里
==========================================================
固定工作流：步骤由代码预先确定。
Agent：下一步做什么，由模型根据运行结果决定。两种方式可以混合。

本文件用"脚本化决策器"代替模型，只观察控制循环本身：
状态、节点、边、终止条件、失败出口，以及暂停与恢复。不调用任何模型。

本文件用到的 LangGraph 写法（StateGraph、条件边、检查点）会在 4.2、4.3、4.10 逐步讲解。
现在把它们当作"描述流程图的语言"即可：读懂每个节点做什么、每条边怎么走。

前置：1.5（工具调用的两轮流程）
运行：python tools/run_chapter.py 4.1（离线）
输出：固定工作流的结果，以及两次有界循环：正常结束、预算耗尽
对应测试：python -m pytest chapters/test_new_lessons.py -q
==========================================================
"""

from __future__ import annotations

from typing import Callable, Literal, TypedDict

from langgraph.graph import END, START, StateGraph


# ---------- 1. 状态：图在节点之间传递的数据 ----------
class Decision(TypedDict):
    """决策器给出的下一步动作：调用 add 工具，或者结束。"""

    action: Literal["add", "finish"]
    a: int
    b: int


class State(TypedDict):
    question: str
    steps: int                   # 已执行的工具次数，用来限制预算
    observations: list[int]      # 工具返回的结果，只追加、不覆盖
    decision: Decision           # 最近一次决策
    status: Literal["running", "done", "failed"]
    error: str                   # 失败原因；没有失败时为空


# ---------- 2. 固定工作流：步骤由代码写死 ----------
def fixed_workflow(a: int, b: int) -> int:
    """顺序由代码预先确定：验证输入，执行一次加法。没有"决定下一步"这回事。"""
    if type(a) is not int or type(b) is not int:   # 拒绝 bool 和字符串
        raise ValueError("输入必须是整数")
    return a + b


# ---------- 3. 决策器：真实系统里由模型担任，这里用脚本代替 ----------
def scripted_planner(state: State) -> Decision:
    """还没有观察结果就要求 add；已有结果就结束。"""
    return {"action": "finish" if state["observations"] else "add", "a": 2, "b": 3}


# ---------- 4. 用图搭出"决策 → 工具 → 决策"的有界循环 ----------
def build_graph(
    planner: Callable[[State], Decision] = scripted_planner,
    *,
    max_steps: int = 2,          # 工具调用次数上限：循环必须有出口
    checkpointer=None,           # 检查点：让图能暂停后恢复，4.10 详细讲
    pause_before_tool: bool = False,  # 是否在执行工具前暂停，等人确认
):
    if max_steps < 1:
        raise ValueError("max_steps 必须大于 0")

    def decide(state: State) -> dict:
        """决策节点：请求下一步动作，并检查工具白名单和预算。节点返回的是"要更新的字段"。"""
        try:
            choice = planner(state)
        except (ValueError, TimeoutError) as exc:   # 只处理已声明的可预期错误，意外错误向外暴露
            return {"status": "failed", "error": str(exc)}
        if choice.get("action") == "finish":
            return {"decision": choice, "status": "done"}
        if choice.get("action") != "add":            # 白名单：只允许 add
            return {"status": "failed", "error": "工具不在白名单"}
        if state["steps"] >= max_steps:              # 预算耗尽：不再执行工具
            return {"status": "failed", "error": "工具步数预算耗尽"}
        return {"decision": choice, "status": "running"}

    def tool(state: State) -> dict:
        """工具节点：校验参数并执行；没有外部副作用。结果追加到 observations，步数加一。"""
        try:
            choice = state["decision"]
            value = fixed_workflow(choice.get("a"), choice.get("b"))
        except ValueError as exc:                    # 参数错误：记为失败，不伪装成成功
            return {"steps": state["steps"] + 1, "status": "failed", "error": str(exc)}
        return {
            "steps": state["steps"] + 1,
            "observations": [*state["observations"], value],   # 返回新列表，不原地修改旧状态
        }

    graph = StateGraph(State)
    graph.add_node("decide", decide)
    graph.add_node("tool", tool)
    graph.add_edge(START, "decide")                  # 入口：先决策
    # 条件边：决策后如果仍在运行就去执行工具，否则（完成或失败）结束
    graph.add_conditional_edges(
        "decide", lambda state: "tool" if state["status"] == "running" else END
    )
    # 工具执行后：失败则结束，成功则回到决策节点，形成循环
    graph.add_conditional_edges(
        "tool", lambda state: END if state["status"] == "failed" else "decide"
    )
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["tool"] if pause_before_tool else [],   # 在 tool 节点前暂停
    )


def initial_state() -> State:
    return {
        "question": "计算2加3",
        "steps": 0,
        "observations": [],
        "decision": {"action": "finish", "a": 0, "b": 0},
        "status": "running",
        "error": "",
    }


if __name__ == "__main__":
    print("固定工作流：", fixed_workflow(2, 3))
    for name, graph in (
        ("正常循环", build_graph()),   # 先 add，看到结果后 finish → done
        # 决策器一直要求 add：第 3 次决策时预算耗尽 → failed，不会无限循环
        ("预算耗尽", build_graph(lambda _: {"action": "add", "a": 2, "b": 3})),
    ):
        result = graph.invoke(initial_state())
        print(name, result["status"], result["observations"], result["error"])
