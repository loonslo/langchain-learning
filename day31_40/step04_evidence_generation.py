"""Step 4 / Day37-38：为购车决策接入真实搜索和安全 Text2SQL。

阅读顺序：adapters 初始化 → route/plan → specialist → compose_context → generate。
重点不是“模型会写 SQL”，而是模型输出必须经过确定性安全门才允许碰数据库。

给初学者的总览：Step2 的 specialist 只是让模型说明“应该查什么”，本步才真正接入两个数据源：
web（联网搜索）和 sql（本地 SQLite）。两个数据源虽然底层实现不同，但都通过 collect(instruction)
返回统一的 Evidence 格式，Graph 因此只负责编排，不必知道 HTTP、SQLite 的具体 SDK 细节。

安全主线：模型可以提出 SQL，但不能直接执行 SQL。SafeSqlAdapter 会先限制语句类型、危险关键字、
表名白名单和 LIMIT，再以只读连接查询；任何不满足规则的 SQL 都在工具边界被拒绝。
"""

from __future__ import annotations

import json  # 把流式 State/节点更新写成 JSONL 报告。
import operator  # 为 Reducer 字段提供 operator.add。
import os  # 读取数据库路径等环境变量。
import time  # 记录每个节点耗时。
from pathlib import Path  # 处理数据库和报告文件路径。
from typing import Annotated, Protocol, TypedDict  # 声明共享状态和可替换模型接口。

from langgraph.graph import END, START, StateGraph  # LangGraph 的构图 API。

from .adapters import ResilientAdapter, SafeSqlAdapter, TavilySearchAdapter, init_car_database
# ResilientAdapter 负责超时/重试/降级；后两个适配器分别连接真实搜索和只读 SQLite。
from .production_graph import (
    DeepSeekGateway, Evidence, RouteDecision, TraceEvent, UnavailableAdapter, WorkItem, _event,
)
# production_graph.py 提供共享的数据契约、真实模型网关和统一的 trace 事件格式。


class GraphState(TypedDict):
    """Step4 的共享状态，也就是所有节点之间传递的数据包。"""

    # 用户输入和 route 是前置节点产生的基础信息。
    question: str
    route: dict
    # plan 生成完整任务；completed_items 记录循环中已经处理过的任务 id。
    work_items: list[dict]
    completed_items: Annotated[list[str], operator.add]
    # Web 摘要和 SQL rows 最终都变成相同 Evidence 契约。
    evidence: Annotated[list[Evidence], operator.add]
    errors: Annotated[list[str], operator.add]
    # trace 与 errors 互补：errors 只覆盖失败路径，trace 还记录成功路径的节点顺序与耗时。
    # 本步首次接入真实 I/O（搜索/SQLite），两者合起来才能回答「谁慢了、谁降级了」。
    trace: Annotated[list[TraceEvent], operator.add]
    # 主管循环轮次，用于兜住「计划失控」时的预算护栏（与 Step5 / 完整版一致）。
    supervisor_steps: int
    # compose_context 生成给模型的统一文本，以及 generate 生成的最终文本。
    context: str
    final_answer: str


class ModelGateway(Protocol):
    """Graph 依赖的模型最小接口。

    真实实现是 DeepSeekGateway；测试时可以注入假模型，让 route/plan/generate_sql 返回固定结果，
    从而在不访问网络的情况下验证安全门和图的分支。
    """

    def route(self, question: str, history_view: str) -> RouteDecision: ...
    # 计划交给模型，才能让每个数据源拿到聚焦的 instruction，而不是原始问句。
    def plan(self, question: str, decision: RouteDecision) -> list[WorkItem]: ...
    def generate(self, question: str, history_view: str, context: str, feedback: str) -> str: ...
    def generate_sql(self, question: str, schema: str) -> str: ...


# 主管循环的预算护栏：计划条数由模型决定，必须限制轮数上限，防止长循环。
# 这里限制的是 supervisor 进入循环的轮数，不是单个 SQL 的 LIMIT；两者保护对象不同。
MAX_SUPERVISOR_STEPS = 10


def build_graph(model: ModelGateway | None = None):
    """构建 Step4 图，并在构图时准备真实数据源适配器。"""

    # 不传 model 时默认使用真实 DeepSeekGateway；传入假模型时不会触发真实模型调用。
    model = model or DeepSeekGateway()
    # DAY31_40_DB 允许把数据库放到指定位置；没有配置时使用当前示例目录下的 data/car_decision.db。
    db_path = Path(os.getenv("DAY31_40_DB", str(Path(__file__).parent / "data" / "car_decision.db")))
    # 这里只创建表结构，不填入虚构的家庭或车型数据；真实记录需要由外部流程写入并核验。
    init_car_database(db_path)
    # Graph 只依赖 collect()；真实 SDK、超时和降级都藏在适配器边界内。
    adapters = {
        # web 失败后使用 UnavailableAdapter，返回带 warning 的诚实占位证据，而不是编造搜索结果。
        "web": ResilientAdapter(TavilySearchAdapter(), UnavailableAdapter("web"), max_attempts=3),
        # sql 同样有重试/降级，但 SafeSqlAdapter 还额外负责 SQL 生成后的安全校验和只读执行。
        "sql": ResilientAdapter(SafeSqlAdapter(db_path, model), UnavailableAdapter("sql"), max_attempts=2),
    }

    def intake(state: GraphState) -> dict:
        """入口节点：清洗问题并拒绝空输入。"""

        # 统一空白能减少 Prompt 噪声；节点只返回 question，其他 State 字段保持原值。
        question = " ".join(state["question"].split())
        if not question:
            raise ValueError("问题不能为空")
        return {"question": question}

    def route(state: GraphState) -> dict:
        """路由节点：决定本次请求允许访问哪些数据源。"""

        started = time.perf_counter()
        decision = model.route(state["question"], "")
        # Step4 只开放 web/sql。即使模型选 MCP，也不能越过程序白名单。
        sources = [source for source in decision.sources if source in adapters]
        dropped = [source for source in decision.sources if source not in adapters]
        # 被白名单挡掉的数据源必须留痕，否则「路由说要查、最后却没查」对用户完全不可见。
        detail = f"intent={decision.intent}, sources={sources}"
        if dropped:
            detail += f"；已拦截未开放数据源：{dropped}"
        return {"route": decision.model_copy(update={"sources": sources}).model_dump(),
                "errors": [f"数据源未开放，已拦截：{dropped}"] if dropped else [],
                "trace": _event("route", detail, started)}

    def plan(state: GraphState) -> dict:
        """把路由结果变成按数据源拆开的取证任务。"""

        # 不同 parallel_group 在本步按顺序执行；Step5 再真正并行派发同组任务。
        started = time.perf_counter()
        decision = RouteDecision.model_validate(state["route"])
        # 计划交给模型：每个数据源拿到「聚焦」的 instruction，而不是把原始问句原样透传。
        # 这直接影响 SQL 生成质量——混合意图的原始问句会让 generate_sql 产出不稳的 SQL。
        items = [item for item in model.plan(state["question"], decision)
                 if item.source in adapters]
        if not items:
            # 兜底：模型没给出可用任务时，仍按路由批准的数据源各建一个任务，
            # 避免「路由说要查、计划却为空」导致静默无证据生成。
            items = [WorkItem(id=f"task-{i}", source=source,
                              instruction=state["question"], parallel_group=i)
                     for i, source in enumerate(decision.sources)]
        # 本步顺序执行，统一重排为 0-based 连续组，与 Step5 / 完整版语义一致。
        items = [item.model_copy(update={"parallel_group": i})
                 for i, item in enumerate(items)]
        # 任务最终存成 dict 列表，便于 State 序列化；WorkItem 的字段仍会在 specialist 中再次校验。
        return {"work_items": [item.model_dump() for item in items],
                "trace": _event("plan", f"生成 {len(items)} 个取证任务", started)}

    def after_route(state: GraphState) -> str:
        """路由后的确定性分支：越界/受限/缺信息优先，合法请求才进入取证。"""

        decision = RouteDecision.model_validate(state["route"])
        if not decision.in_scope:
            return "out_of_scope"
        if decision.requires_approval:
            return "restricted_action"
        if decision.missing_information:
            return "clarify"
        return "plan" if decision.sources else "generate"

    def clarify(state: GraphState) -> dict:
        """缺少必要信息时直接追问，不让工具在条件不足时查询。"""

        missing = RouteDecision.model_validate(state["route"]).missing_information
        return {"final_answer": "开始真实取证前，请补充：" + "、".join(missing) + "。"}

    def out_of_scope(state: GraphState) -> dict:
        """越界分支：不访问任何外部数据源。"""

        return {"final_answer": "当前步骤只处理家庭购车的公开资料与已录入数据。"}

    def restricted_action(state: GraphState) -> dict:
        """受限动作分支：本步只有查询能力，不执行下单、贷款或付款。"""

        return {"final_answer": "本步骤只能查询资料，不能执行下单、贷款或付款。"}

    def supervisor(state: GraphState) -> dict:
        """监督节点：推进顺序执行循环，并记录是否触发轮次预算。"""

        started = time.perf_counter()
        step = state["supervisor_steps"] + 1
        completed = set(state["completed_items"])
        pending = [item for item in state["work_items"] if item["id"] not in completed]
        # 预算护栏：计划条数由模型决定，必须兜住「计划失控」导致的长循环。
        budget_hit = step > MAX_SUPERVISOR_STEPS
        return {"supervisor_steps": step,
                "trace": _event("supervisor", f"第 {step} 轮，待执行 {len(pending)} 项"
                                + ("（预算护栏触发）" if budget_hit else ""), started)}

    def dispatch(state: GraphState) -> str:
        """条件边：还有任务就派给 specialist，全部完成或超预算就汇总。"""

        completed = set(state["completed_items"])
        if state["supervisor_steps"] > MAX_SUPERVISOR_STEPS:
            return "compose_context"
        return "specialist" if any(item["id"] not in completed for item in state["work_items"]) else "compose_context"

    def specialist(state: GraphState) -> dict:
        """取证节点：通过统一适配器执行当前 WorkItem。"""

        completed = set(state["completed_items"])
        # model_validate 把 State 中的普通 dict 还原成 WorkItem，并检查 source/instruction 等字段形状。
        item = WorkItem.model_validate(next(x for x in state["work_items"] if x["id"] not in completed))
        started = time.perf_counter()
        try:
            # SQL adapter 内部顺序：生成 SQL → 校验 → 只读连接 → rows。
            # 对 web 来说，collect() 则是搜索；Graph 不需要写两套调用逻辑。
            result = adapters[item.source].collect(item.instruction)
            degraded = any(entry.get("warning") for entry in result)
            return {"completed_items": [item.id], "evidence": result,
                    "trace": _event("specialist",
                                    f"{item.id}/{item.source} 返回 {len(result)} 条"
                                    + ("（已降级）" if degraded else ""), started)}
        except Exception as exc:
            # 本教学图把失败任务标记为 completed，保证 Supervisor 不会无限重复同一个失败任务；
            # 同时把异常类型写入 errors，调用方仍能知道本次结果不完整。生产系统可按错误类型细分重试策略。
            return {"completed_items": [item.id], "errors": [f"{item.source}: {type(exc).__name__}"],
                    "trace": _event("specialist",
                                    f"{item.id}/{item.source} 失败：{type(exc).__name__}", started)}

    def compose_context(state: GraphState) -> dict:
        """把不同来源的 Evidence 整理成一个带来源、引用和警告的 Prompt 上下文。"""

        # reference 必须和内容一起进入上下文，最终答案才能追溯来源。
        started = time.perf_counter()
        blocks = []
        for i, item in enumerate(state["evidence"], 1):
            # source 必须保留：generate 的提示词要求「区分实时公开资料、用户录入数据」，
            # 上下文里没有来源标记，模型无从区分（本步同时有 web 与 sql 两种真实来源）。
            # warning 也必须保留：降级证据若不带警告，模型会把「搜索暂不可用」这类
            # 占位内容当作真资料，进而编造——这是诚实降级的最后一道防线。
            warning = f"\n警告：{item['warning']}" if item.get("warning") else ""
            blocks.append(f"[{i}] ({item['source']}) {item['title']}\n{item['content']}"
                          f"\n来源：{item['reference']}{warning}")
        return {"context": "\n\n".join(blocks),
                "trace": _event("compose_context", f"汇聚 {len(blocks)} 条证据", started)}

    def generate(state: GraphState) -> dict:
        """只根据已整理的证据生成答案，不在此节点查询工具。"""

        # generate 不知道证据来自网页还是数据库，只消费统一 context。
        started = time.perf_counter()
        answer = model.generate(state["question"], "", state["context"], "")
        return {"final_answer": answer,
                "trace": _event("generate", f"生成 {len(answer)} 字答案", started)}

    # 节点负责“做什么”，边负责“下一步什么时候走”；分开写能让流程图和业务代码都更清晰。
    graph = StateGraph(GraphState)
    for name, node in [("intake", intake), ("route", route),
                       ("clarify", clarify), ("out_of_scope", out_of_scope),
                       ("restricted_action", restricted_action), ("plan", plan),
                       ("supervisor", supervisor), ("specialist", specialist),
                       ("compose_context", compose_context), ("generate", generate)]:
        graph.add_node(name, node)
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "route")
    graph.add_conditional_edges("route", after_route,
                                {"clarify": "clarify", "out_of_scope": "out_of_scope",
                                 "restricted_action": "restricted_action",
                                 "plan": "plan", "generate": "generate"})
    graph.add_edge("clarify", END)
    graph.add_edge("out_of_scope", END)
    graph.add_edge("restricted_action", END)
    graph.add_edge("plan", "supervisor")
    graph.add_conditional_edges("supervisor", dispatch,
                                {"specialist": "specialist", "compose_context": "compose_context"})
    graph.add_edge("specialist", "supervisor")
    graph.add_edge("compose_context", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def initial_state(question: str) -> GraphState:
    """为一次新的 Step4 运行准备空容器。"""

    # completed_items/evidence/errors/trace 都是追加型字段，从空列表开始最容易理解，
    # 也保证第一次循环不会误判已有任务或证据。
    return {"question": question, "route": {}, "work_items": [], "completed_items": [],
            "evidence": [], "errors": [], "trace": [], "supervisor_steps": 0,
            "context": "", "final_answer": ""}


def run(question: str, stream_mode: str = "updates",
        trace_path: str = "reports/day31_40_step04.jsonl") -> dict:
    """运行并落盘 JSONL，便于跨运行对比各节点耗时与降级情况。

    本步接入真实 I/O（搜索/SQLite），节点耗时波动大，只看单次打印无法定位慢点。
    """
    app = build_graph()
    # updates 返回节点本轮写入的增量，final 用来在函数结束时把这些增量合并成可返回的状态。
    final: dict = dict(initial_state(question))
    path = Path(trace_path)
    # 报告目录不存在时自动创建，默认示例可以直接运行。
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        # updates 看增量；values 看完整 State；debug 看底层调度。
        for chunk in app.stream(initial_state(question), stream_mode=stream_mode):
            # ensure_ascii=False 保留中文；default=str 让少数非 JSON 原生对象也能写入日志。
            line = json.dumps(chunk, ensure_ascii=False, default=str)
            output.write(line + "\n")
            print(line)
            if stream_mode == "updates":
                for update in chunk.values():
                    if isinstance(update, dict):
                        final.update(update)
            elif stream_mode == "values" and isinstance(chunk, dict):
                final = chunk
    return final


if __name__ == "__main__":
    result = run("搜索燃油、纯电和插混的最新用车资料，并查询我已录入的家庭画像与真实候选车数据")
    print(result["final_answer"])
    for event in result["trace"]:
        print(f"[trace] {event['node']}: {event['detail']} ({event['duration_ms']}ms)")
