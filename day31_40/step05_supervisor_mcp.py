"""Step 5 / Day39-40：购车专家 Supervisor、动态 fan-out、Reducer 和真实 MCP。

阅读顺序：plan → supervisor/dispatch → Send → specialist → Reducer 汇聚。
与 Step4 的关键差别：同一 parallel_group 不再串行，而是动态并行执行。

给初学者的总览：plan 先把总问题拆成多个 WorkItem；Supervisor 决定这一轮要执行哪个依赖组；
dispatch 返回多个 Send 后，LangGraph 会为同组任务同时启动多个隔离的 specialist。
specialist 各自返回结果，Reducer 再把这些结果合并回主 State，Supervisor 继续检查下一组。

MCP 在本文件里通过 build_online_services() 提供的适配器接入。Graph 只看到统一的 collect() 接口，
不需要知道 MCP Tools、Resources、Prompts 的具体协议细节；这就是“外部系统放在适配器边界”的意义。
"""

from __future__ import annotations

import operator  # 用 operator.add 把并行节点的列表结果合并起来。
import time  # 记录节点耗时，便于观察并行执行效果。
import uuid  # 为每次请求生成唯一 request_id，隔离不同运行的数据。
from typing import Annotated, TypedDict  # 声明 Reducer 字段和共享 State 的结构。

from langgraph.graph import END, START, StateGraph  # 图的起点、终点和构图器。
from langgraph.types import Send  # 动态 fan-out：把多个任务分别发送给同一个节点。

from .production_graph import (
    Evidence, ProductionServices, RouteDecision, TraceEvent, WorkItem, _event,
    build_online_services,
)


class GraphState(TypedDict):
    """主图状态：保存计划、并行进度、证据和最终答案。"""

    # request_id 不只是日志字段：后面 compose_context 会用它过滤本次请求的证据。
    request_id: str
    question: str
    route: dict
    # work_items 是全量计划；它本身不使用 Reducer，因为只由 plan 节点一次性写入。
    work_items: list[dict]
    # 并行 specialist 会在同一 super-step 写这些字段，必须配置 Reducer。
    # operator.add 让多个 specialist 的 [id] 追加成一个列表，而不是互相覆盖。
    completed_items: Annotated[list[str], operator.add]
    evidence: Annotated[list[Evidence], operator.add]
    errors: Annotated[list[str], operator.add]
    # 并行 fan-out 时多个 specialist 会在同一 super-step 写 trace，必须配置 Reducer。
    trace: Annotated[list[TraceEvent], operator.add]
    # supervisor_steps 是循环计数器；两个 max 字段是防止并行任务无限扩张的预算护栏。
    supervisor_steps: int
    max_supervisor_steps: int
    max_tool_calls: int
    context: str
    final_answer: str


def build_graph(services: ProductionServices | None = None):
    """构建 Step5 图。

    services 默认连接真实 DeepSeek/Tavily/SQLite/MCP，也可在测试中注入一组假服务。
    注入整个 services 对象的好处是模型和所有适配器都能一次替换，图的编排逻辑保持不变。
    """

    # 不传入时才创建真实在线服务；测试调用 build_graph(fake_services) 不会连外部系统。
    services = services or build_online_services()

    def intake(state: GraphState) -> dict:
        """入口节点：清理问题，并用 request_id 把本次运行写进 trace。"""

        started = time.perf_counter()
        # 和前面步骤一样，先规整空白；Step5 额外限制最大长度，防止过大的输入拖垮整个并行流程。
        question = " ".join(state["question"].split())
        if not question or len(question) > 2000:
            raise ValueError("问题不能为空且不能超过 2000 字")
        return {"question": question,
                "trace": _event("intake", f"request_id={state['request_id'][:8]}", started)}

    def route(state: GraphState) -> dict:
        """路由节点：让模型选择意图和需要的数据源。"""

        started = time.perf_counter()
        # history_view 暂时为空；本步重点是并行取证和 MCP，不展开多轮历史管理。
        decision = services.model.route(state["question"], "")
        return {"route": decision.model_dump(),
                "trace": _event("route", f"intent={decision.intent}, sources={decision.sources}", started)}

    def plan(state: GraphState) -> dict:
        """生成并清洗并行任务计划。"""

        # WorkItem.parallel_group 决定依赖关系：同组可并行，后续组等待前组。
        started = time.perf_counter()
        decision = RouteDecision.model_validate(state["route"])
        items = services.model.plan(state["question"], decision)
        # 与 Product Graph 一致：任务 ID 带请求前缀，并在进入并行调度前去重。
        prefix = state["request_id"][:8]
        # 模型可能意外返回重复 id；先加请求前缀，再用 seen 去重，避免同一请求内部重复执行。
        seen: set[str] = set()
        unique: list[WorkItem] = []
        for item in items:
            stable_id = f"{prefix}:{item.id}"
            if stable_id not in seen:
                seen.add(stable_id)
                unique.append(item.model_copy(update={"id": stable_id}))
        # State 里保存可序列化 dict；specialist 收到后会再次 model_validate 成 WorkItem。
        return {"work_items": [item.model_dump() for item in unique],
                "trace": _event("plan", f"生成 {len(unique)} 个任务", started)}

    def after_route(state: GraphState) -> str:
        """路由后的确定性分支：合法请求才进入计划阶段。"""

        decision = RouteDecision.model_validate(state["route"])
        if not decision.in_scope:
            return "out_of_scope"
        if decision.missing_information:
            return "clarify"
        # requires_approval 不等于禁止取证；Product Graph 会在生成和质检后处理人工审批。
        # 本教学步到 generate 就结束，所以这里不提前把“需要审批”当作拒绝。
        return "plan"

    def clarify(state: GraphState) -> dict:
        """信息不足时提前结束，避免启动无意义的并行任务。"""

        missing = RouteDecision.model_validate(state["route"]).missing_information
        return {"final_answer": "并行取证和成本计算前，请补充：" + "、".join(missing) + "。"}

    def out_of_scope(state: GraphState) -> dict:
        """越界分支：不进入计划和工具调用。"""

        return {"final_answer": "当前步骤只处理家庭购车取证与成本计算。"}

    def supervisor(state: GraphState) -> dict:
        """监督节点：计算预算和待办数量，不亲自调用任何业务工具。"""

        started = time.perf_counter()
        step = state["supervisor_steps"] + 1
        work_ids = {item["id"] for item in state["work_items"]}
        # 只统计本轮计划内的 id，避免旧运行或异常输入中的 id 干扰当前进度判断。
        completed = set(state["completed_items"]) & work_ids
        pending = [item for item in state["work_items"] if item["id"] not in completed]
        # 两个预算分别限制“循环轮数”和“工具任务数”；任一耗尽都停止继续派工。
        budget_hit = (step > state["max_supervisor_steps"]
                      or len(completed) >= state["max_tool_calls"])
        updates: dict = {
            "supervisor_steps": step,
            "trace": _event("supervisor", "预算护栏触发" if budget_hit
                            else f"第 {step} 轮，待执行 {len(pending)} 项", started),
        }
        if budget_hit:
            # errors 使用 Reducer 追加，compose_context 之后调用方仍能看到停止原因。
            updates["errors"] = ["Supervisor/工具调用预算耗尽，停止继续委派"]
        return updates

    def dispatch(state: GraphState):
        """把当前最早依赖组动态派发给 specialist，或进入汇总节点。"""

        work_ids = {item["id"] for item in state["work_items"]}
        completed = set(state["completed_items"]) & work_ids
        pending = [WorkItem.model_validate(item) for item in state["work_items"]
                   if item["id"] not in completed]
        budget_hit = (state["supervisor_steps"] > state["max_supervisor_steps"]
                      or len(completed) >= state["max_tool_calls"])
        if not pending or budget_hit:
            # 没有待办或预算耗尽都不能再发 Send；直接汇总已有证据，并由答案提示数据可能不完整。
            return "compose_context"
        # 只选择最早的未完成组，保证依赖前序结果的任务不会提前运行。
        group = min(item.parallel_group for item in pending)
        # 隔离不等于断开依赖：后续组可收到精简的前序证据，但看不到完整主 State。
        prerequisites = [
            f"({entry['source']}) {entry['title']}: {entry['content'][:800]}"
            for entry in state["evidence"]
            if entry.get("request_id") == state["request_id"]
        ]
        dependency_context = "\n".join(prerequisites) if group > 0 else ""
        # 即使是后续组，也只接收前序证据的精简文本；这样既保留依赖，又避免把主 State 全量复制给 worker。
        remaining = max(0, state["max_tool_calls"] - len(completed))
        # 返回多个 Send：LangGraph 为每个任务创建一个隔离的 specialist 输入。
        # 切片 remaining 是第二层护栏，防止一次计划包含过多并行工具调用。
        return [Send("specialist", {"item": item.model_dump(),
                                    "request_id": state["request_id"],
                                    "dependency_context": dependency_context})
                for item in pending if item.parallel_group == group][:remaining]

    def specialist(worker_state: dict) -> dict:
        """执行一个隔离的取证 worker，并把结果作为增量返回给主图。"""

        # 子 Agent 只看一个 WorkItem，不读取主 Graph 的完整上下文，这就是上下文隔离。
        item = WorkItem.model_validate(worker_state["item"])
        started = time.perf_counter()
        try:
            instruction = item.instruction
            if worker_state.get("dependency_context"):
                # 后续依赖组需要前序结果时，显式把精简上下文拼入指令；没有依赖时保持原指令不变。
                instruction += ("\n\n使用这些前序证据参数计算；缺参数必须说明：\n"
                                + worker_state["dependency_context"])
            # source 决定实际适配器：可能是 web、sql 或 mcp，但 specialist 不需要写分支调用代码。
            result = services.adapters[item.source].collect(instruction)
            # request_id 随证据一起保存，后续汇总时可以过滤出本次请求的结果。
            evidence = [{**entry, "request_id": worker_state["request_id"]} for entry in result]
            degraded = any(entry.get("warning") for entry in evidence)
            return {"completed_items": [item.id], "evidence": evidence,
                    "trace": _event("specialist",
                                    f"{item.id}/{item.source} 返回 {len(evidence)} 条"
                                    + ("（已降级）" if degraded else ""), started)}
        except Exception as exc:
            # 记录失败但仍标记当前任务完成，避免失败任务被 Supervisor 无限重新派发；
            # errors 会让调用方知道结果不完整，生产系统可按错误类型增加更细的重试/人工处理。
            return {"completed_items": [item.id],
                    "errors": [f"{item.id}/{item.source}: {type(exc).__name__}"],
                    "trace": _event("specialist",
                                    f"{item.id}/{item.source} 失败：{type(exc).__name__}", started)}

    def compose_context(state: GraphState) -> dict:
        """并行 fan-out 的 fan-in：等待各 worker 返回后统一整理证据。"""

        # 所有并行 Send 完成后，Reducer 已把 evidence 合并好，再统一生成答案。
        started = time.perf_counter()
        # 过滤 request_id 是一道边界保护：主图状态可能被复用或包含其他请求的历史数据。
        current = [item for item in state["evidence"]
                   if item.get("request_id") == state["request_id"]]
        blocks = []
        for i, item in enumerate(current, 1):
            warning = f"\n警告：{item['warning']}" if item.get("warning") else ""
            blocks.append(f"[{i}] ({item['source']}) {item['title']}\n{item['content']}"
                          f"\n来源：{item['reference']}{warning}")
        return {"context": "\n\n".join(blocks),
                "trace": _event("compose_context", f"汇聚 {len(blocks)} 条证据", started)}

    def generate(state: GraphState) -> dict:
        """消费汇总证据并生成本教学步的最终答案。"""

        started = time.perf_counter()
        answer = services.model.generate(state["question"], "", state["context"], "")
        # Step5 到此直接交付；Product Graph 会把这里扩展成 draft → 质检 → 审批 → publish。
        return {"final_answer": answer,
                "trace": _event("generate", f"生成 {len(answer)} 字答案", started)}

    # 下面的节点描述“每一步做什么”，边描述“何时进入下一步”。
    graph = StateGraph(GraphState)
    for name, node in [("intake", intake), ("route", route),
                       ("clarify", clarify), ("out_of_scope", out_of_scope),
                       ("plan", plan), ("supervisor", supervisor),
                       ("specialist", specialist), ("compose_context", compose_context), ("generate", generate)]:
        graph.add_node(name, node)
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "route")
    graph.add_conditional_edges("route", after_route,
                                {"clarify": "clarify", "out_of_scope": "out_of_scope",
                                 "plan": "plan"})
    graph.add_edge("clarify", END)
    graph.add_edge("out_of_scope", END)
    graph.add_edge("plan", "supervisor")
    # dispatch 可以返回一个字符串（直接汇总），也可以返回多个 Send（并行派工），所以目标列表包含两种出口。
    graph.add_conditional_edges("supervisor", dispatch, ["specialist", "compose_context"])
    # 专家完成后回主管；主管检查下一组或进入 compose_context。
    graph.add_edge("specialist", "supervisor")
    graph.add_edge("compose_context", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def initial_state(question: str) -> GraphState:
    """创建一份独立请求的初始状态。"""

    # 每次运行都生成新 request_id，避免并行任务把不同请求的 evidence 混在一起。
    return {"request_id": str(uuid.uuid4()), "question": question,
            "route": {}, "work_items": [], "completed_items": [],
            "evidence": [], "errors": [], "trace": [], "supervisor_steps": 0,
            # 12 轮限制循环深度，8 次限制并行工具任务数；它们是本示例的成本/安全护栏。
            "max_supervisor_steps": 12, "max_tool_calls": 8,
            "context": "", "final_answer": ""}


if __name__ == "__main__":
    result = build_graph().invoke(initial_state(
        "查询家庭画像和候选车，搜索最新公开资料，并用 MCP 比较月供、年度能源费和五年总成本"
    ), {"recursion_limit": 30})
    print(result["final_answer"])
    for event in result["trace"]:
        print(f"[trace] {event['node']}: {event['detail']} ({event['duration_ms']}ms)")
