"""Step 3 / Day35-36：家庭多轮讨论、checkpoint 与购车报告确认。

阅读顺序：history 三个字段 → manage_context → approval → run() 的两次 invoke。
重点理解：interrupt 保存的是可恢复状态，不是让 Python 进程一直阻塞等待。

给初学者的总览：本步把“一次请求一次回答”升级成“可以暂停、等待人确认、再继续”的流程。
图先整理对话历史，再生成购车建议草稿；如果需要审批，就在 approval 节点暂停。
审批人输入 approve / reject 后，程序使用同一个 thread_id 恢复 checkpoint 中保存的状态，
最后由 publish 生成确认结果。这里的 publish 仍只是保存/返回建议，不会真的下单、贷款或付款。
"""

from __future__ import annotations

import operator  # 为对话历史配置追加型 Reducer。
import uuid  # 为每次运行生成不会和其他会话冲突的 thread_id。
from typing import Annotated, Literal, Protocol, TypedDict  # 声明状态字段和模型替换接口。

from langgraph.graph import END, START, StateGraph  # 构造带起点和终点的状态图。
from langgraph.types import Command, interrupt  # interrupt 暂停图；Command(resume=...) 恢复图。

from .production_graph import DeepSeekGateway, open_checkpointer  # 复用真实模型和 checkpoint 工厂。


class GraphState(TypedDict, total=False):
    """Step3 的共享状态。

    total=False 表示类型层面允许字段暂时缺失；运行时 initial_state 仍会把本步需要的字段初始化好。
    这种写法常见于图：某些字段要等前置节点运行后才有值，例如 draft 要等 generate 之后才出现。
    """

    question: str
    # 完整历史用于审计，永不因为上下文窗口而删除；operator.add 表示新消息追加到旧列表后面。
    conversation_history: Annotated[list[dict[str, str]], operator.add]
    # summary + recent 才是模型视图，控制 Token、延迟和噪声；完整历史不直接塞进 Prompt。
    history_summary: str
    # 表示已经摘要到完整历史的哪个下标，避免每轮重复摘要同一批消息。
    history_summarized_count: int
    # 最近四轮保留原文，给模型提供最新上下文；它是视图，不是审计源。
    recent_history: list[dict[str, str]]
    # generate 产出的待确认文本。
    draft: str
    # 由调用者决定本次流程是否需要人工确认。
    requires_approval: bool
    # 审批状态是有限集合，便于判断流程是否已批准或拒绝。
    approval_status: Literal["not_required", "pending", "approved", "rejected"]
    # publish 最终给调用方的文本。
    final_answer: str


class ModelGateway(Protocol):
    """本步依赖的最小模型接口，方便用假模型做离线测试。"""

    # 历史摘要模型接收“本次新增的旧消息”和“已有摘要”，输出更新后的摘要。
    def summarize_history(self, old_history: list[dict[str, str]], existing: str) -> str: ...
    @property
    def llm(self): ...  # generate 使用底层 LLM 生成草稿。


def build_graph(model: ModelGateway | None = None, checkpointer=None):
    """构建可以暂停/恢复的审批图。

    checkpointer 是关键依赖：interrupt 发生时，LangGraph 要把 State 保存下来；第二次 invoke
    才能根据同一个 thread_id 找回这份 State。调用者可以传内存版，也可以传 SQLite 版。
    """

    # 不传 model 时连接真实 DeepSeek；传入假模型即可避免网络调用。
    model = model or DeepSeekGateway()

    def manage_context(state: GraphState) -> dict:
        """管理长对话：老消息摘要，最近消息保留原文。"""

        history = state.get("conversation_history", [])
        # already 是上一次已经处理到的下标；只处理它之后的新旧消息，避免重复摘要。
        already = state.get("history_summarized_count", 0)
        # 最近 4 条直接交给模型，其余才有资格进入摘要区。
        cutoff = max(0, len(history) - 4)
        # 只摘要“上次尚未摘要、且已经滑出最近四轮窗口”的部分。
        old = history[already:cutoff]
        summary = state.get("history_summary", "")
        if old:
            # summarize_history 负责把多条旧消息压缩成一段摘要；没有旧消息时沿用原摘要。
            summary = model.summarize_history(old, summary)
        # cutoff 记录本轮摘要边界，recent_history 保存最新四条供 generate 使用。
        return {"history_summary": summary, "history_summarized_count": cutoff,
                "recent_history": history[-4:]}

    def generate(state: GraphState) -> dict:
        """根据摘要、最近对话和当前任务生成“待审批草稿”。"""

        # 完整 conversation_history 不直接进入 Prompt，避免历史无限增长；这是“存储”和“模型视图”分离。
        prompt = (f"历史摘要：{state.get('history_summary', '')}\n"
                  f"最近对话：{state.get('recent_history', [])}\n任务：{state['question']}\n"
                  "生成家庭购车需求确认草稿，列出预算、使用场景、已确认条件与待核验项；"
                  "不要声称已经下单、贷款、付款或发布。")
        # draft 先保存草稿，不能直接写 final_answer，因为它还没有经过人工确认。
        return {"draft": str(model.llm.invoke(prompt).content),
                "approval_status": "pending" if state.get("requires_approval") else "not_required"}

    def approval(state: GraphState) -> dict:
        """人工审批节点：需要审批时暂停，不需要审批时直接放行。"""

        if state["approval_status"] == "not_required":
            # 返回空字典表示本节点没有新增状态，下一条边仍可继续执行 publish。
            return {}
        # interrupt 的 payload 会交给审批界面；这里绝不执行真实发布动作。
        decision = interrupt({
            "draft": state["draft"],
            "ask": "家庭成员是否批准采用这份购车建议？approve / reject（不会自动下单）",
        })
        # interrupt 恢复后才会返回用户输入；把输入归一化成图内固定的两个状态值。
        return {"approval_status": "approved" if str(decision).lower() == "approve" else "rejected"}

    def publish(state: GraphState) -> dict:
        """审批结束后的统一出口，并把问答追加到完整历史。"""

        # publish 只表示确认并保存报告，不代表下单、贷款或付款；它也是完整历史的单一写入口。
        final = ("（家庭成员拒绝，购车建议未发布）"
                 if state["approval_status"] == "rejected" else state["draft"])
        # conversation_history 使用 Annotated[list, operator.add]，所以这里只写本轮一条记录，
        # LangGraph 会自动把它追加到旧历史，而不是要求节点自己复制完整列表。
        return {"final_answer": final,
                "conversation_history": [{"question": state["question"], "answer": final}]}

    # 先注册节点，再用边描述固定执行顺序：上下文管理 → 生成草稿 → 审批 → 发布。
    graph = StateGraph(GraphState)
    graph.add_node("manage_context", manage_context)
    graph.add_node("generate", generate)
    graph.add_node("approval", approval)
    graph.add_node("publish", publish)
    graph.add_edge(START, "manage_context")
    graph.add_edge("manage_context", "generate")
    graph.add_edge("generate", "approval")
    graph.add_edge("approval", "publish")
    graph.add_edge("publish", END)
    # HITL 必须有 checkpointer，否则第二次 invoke 无处恢复。
    return graph.compile(checkpointer=checkpointer)


def initial_state(question: str, requires_approval: bool = True) -> GraphState:
    """创建一次新会话的初始状态。

    默认 requires_approval=True 是教学上的安全默认值：先把结果当成草稿，明确经过人确认后再作为最终建议。
    """

    return {"question": question, "conversation_history": [], "history_summary": "",
            "history_summarized_count": 0,
            "recent_history": [], "draft": "", "requires_approval": requires_approval,
            "approval_status": "not_required", "final_answer": ""}


def run(task: str, checkpoint_kind: str = "memory") -> dict:
    """演示一次完整的“暂停 → 人输入 → 恢复”运行。"""

    # thread_id 是 checkpoint 的索引。同一个 id 才能让第二次 invoke 找到第一次暂停的位置。
    thread_id = f"step03:{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}
    # with 负责创建和释放 checkpoint 存储；memory 适合演示，sqlite 可跨进程保留记录。
    with open_checkpointer(checkpoint_kind) as saver:
        app = build_graph(checkpointer=saver)
        # 第一次 invoke 跑到 interrupt 后正常返回，进程并没有卡在节点里。
        paused = app.invoke(initial_state(task), config)
        if "__interrupt__" in paused:
            # interrupt payload 是 approval 节点提交的字典，界面可以用它展示草稿和问题。
            print("草稿：", paused["__interrupt__"][0].value["draft"])
            decision = input("approve / reject > ").strip().lower()
            # 第二次 invoke 使用相同 thread_id，从 checkpoint 的断点继续。
            return app.invoke(Command(resume=decision), config)
        # requires_approval=False 时不会暂停，第一次 invoke 就能走到这里。
        return paused


if __name__ == "__main__":
    print(run("起草一份预算 20 万的家庭购车建议，提交家庭成员审批")["final_answer"])
