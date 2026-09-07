"""Step 2 / Day33-34：在 Step1 同名结构上增加 plan、supervisor 和执行循环。

阅读顺序：新增 State 字段 → plan → supervisor/dispatch → specialist 回环 → trace。
本步仍不接真实搜索和数据库，只产出“待取证计划”，不把模型内容冒充真实车型事实。

给初学者的总览：一次请求会经过“先判断 → 列计划 → 逐项执行 → 汇总 → 生成答案”几个阶段。
这里的 specialist 虽然名字像“专家”，本步实际上只调用模型说明“应该查什么”，并没有真的访问
网页或数据库。这样可以先把 Plan-and-Execute（先规划、再执行）的图结构看懂，再在 Step4 接入真实 I/O。

本文件和 Step1 的关系：Step1 重点是“可靠地选择分支”；本步把其中一个分支继续拆成多个 WorkItem，
并用 Supervisor 反复检查任务是否完成。trace 则把运行过程中的节点信息留下来，方便初学者观察图到底走了几步。
"""

from __future__ import annotations

import json  # 把运行事件序列化成 JSON，便于保存和之后分析。
import operator  # 提供 operator.add，给 Annotated 字段配置“累加”规则。
import time  # 用 perf_counter 测量节点耗时。
from pathlib import Path  # 负责创建报告目录、打开 JSONL 文件。
from typing import Annotated, Protocol, TypedDict  # 为 State 和可替换模型声明类型契约。

from langgraph.graph import END, START, StateGraph  # 图的起点、终点和构图器。

from .production_graph import DeepSeekGateway, Evidence, RouteDecision, WorkItem
# 上面的四个对象来自完整版：真实模型网关、证据格式、路由决策格式和任务格式。
# 本文件只复用数据契约，不把完整版的所有节点一起复制过来。


class GraphState(TypedDict):
    """本步图中所有节点共享的“工作台”。

    可以把 State 想成一份会被节点接力填写的表格：节点读取当前表格，返回自己新增或修改的
    字段，LangGraph 再把增量合并回表格。字段名必须和节点实际读写的名字一致。
    """

    # 用户给出的原始任务；intake 会先把多余空白折叠掉。
    question: str
    route: dict
    # work_items 是完整计划；completed_items 是可恢复的执行进度。
    work_items: list[dict]
    # 同一个任务可能会在循环的不同轮次被处理；因此不能只看 evidence 数量判断进度，
    # 必须用任务 id 记录“哪一项已经完成”。
    completed_items: Annotated[list[str], operator.add]
    # Annotated + operator.add 是 Reducer：节点返回一小段，Graph 负责累计。
    # 例如 specialist 返回 [evidence_a]，下一轮再返回 [evidence_b]，最终 State 会得到
    # [evidence_a, evidence_b]，而不是后一次结果把前一次覆盖掉。
    evidence: Annotated[list[Evidence], operator.add]
    # context 是把多条 evidence 拼成的 Prompt 文本；它不是新的事实，只是统一格式的中间结果。
    context: str
    # generate 节点最终写入给用户看的文本。
    final_answer: str
    # trace 同样用 Reducer，避免每个节点手工复制整份轨迹。
    trace: Annotated[list[dict], operator.add]


class ModelGateway(Protocol):
    """模型网关的最小接口。

    Protocol 只描述“需要哪些方法”，不要求假模型继承这个类。只要测试替身拥有同名方法，
    就可以传给 build_graph；这样构图逻辑不必绑定真实 API，也能单独测试路由和循环。
    """

    # route 负责把自然语言问题转换成结构化的 RouteDecision。
    def route(self, question: str, history_view: str) -> RouteDecision: ...
    # plan 负责把一个总问题拆成多个可执行的 WorkItem。
    def plan(self, question: str, decision: RouteDecision) -> list[WorkItem]: ...
    # generate 在所有证据整理完后负责写最终答案；四个参数分别是问题、历史、上下文和质检反馈。
    def generate(self, question: str, history_view: str, context: str, feedback: str) -> str: ...
    @property
    def llm(self): ...  # 本教学步用底层 LLM 模拟执行 specialist。


def build_graph(model: ModelGateway | None = None):
    """构造并编译 Step2 的 Plan-and-Execute 图。

    model 使用依赖注入：不传时使用真实 DeepSeekGateway，传入假模型时则可以离线学习图的运行顺序。
    函数内部定义节点，是因为这些节点需要共享同一个 model 闭包；节点本身仍然只通过 state 传递业务数据。
    """

    # “or” 表示调用者没有提供替代品时才创建真实网关；测试时传入假模型不会被覆盖。
    model = model or DeepSeekGateway()

    def intake(state: GraphState) -> dict:
        """入口节点：先把用户输入整理成后续节点可以放心使用的形式。"""

        # split() 会按任意空白切分，join() 再用一个空格连接，例如“买车   预算”会变成“买车 预算”。
        question = " ".join(state["question"].split())
        # 空问题直接在入口失败，避免让模型收到无意义 Prompt；本步没有设置长度上限，Step1 有更严格示例。
        if not question:
            raise ValueError("问题不能为空")
        # 节点只返回修改过的字段，其他字段由 LangGraph 保留原值。
        return {"question": question}

    def route(state: GraphState) -> dict:
        """路由节点：先判断“要不要规划”，而不是立刻执行或生成答案。"""

        # history_view 先传空字符串，因为 Step2 尚未引入对话历史；参数位置保留是为了兼容统一网关接口。
        decision = model.route(state["question"], "")
        # RouteDecision 是 Pydantic 对象，model_dump() 把它转换成可以放进 GraphState 的普通 dict。
        return {"route": decision.model_dump()}

    def plan(state: GraphState) -> dict:
        """把路由结果转换为结构化任务列表。

        计划必须是 WorkItem 列表，不能是一段之后还要靠字符串切割的文字；结构化任务才能被
        Supervisor 通过 id 精确追踪，也才能在后续步骤按 source 和 parallel_group 调度。
        """

        started = time.perf_counter()
        # State 里保存的是 dict，model.plan 需要的是 RouteDecision，所以这里先做一次校验和还原。
        decision = RouteDecision.model_validate(state["route"])
        items = model.plan(state["question"], decision)
        # model_dump() 将每个 WorkItem 转成 dict，方便 LangGraph 序列化、保存和跨节点传递。
        return {"work_items": [item.model_dump() for item in items],
                "trace": [{"node": "plan", "duration_ms": round((time.perf_counter()-started)*1000)}]}

    def after_route(state: GraphState) -> str:
        """根据路由结果选择下一节点；这是纯 Python 的确定性条件边。"""

        decision = RouteDecision.model_validate(state["route"])
        # 判断顺序体现业务优先级：越界先拒绝，敏感动作再拦截，缺信息先追问，最后才进入规划/生成。
        if not decision.in_scope:
            return "out_of_scope"
        if decision.requires_approval:
            return "restricted_action"
        if decision.missing_information:
            return "clarify"
        return "plan" if decision.sources else "generate"

    def clarify(state: GraphState) -> dict:
        """缺少必要条件时提前结束，告诉用户还需要补充哪些字段。"""

        # 这里不让模型自由发挥，而是直接使用结构化字段拼出追问，结果更稳定。
        missing = RouteDecision.model_validate(state["route"]).missing_information
        return {"final_answer": "制定购车比较计划前，请补充：" + "、".join(missing) + "。"}

    def out_of_scope(state: GraphState) -> dict:
        """越界分支：当前教学图只负责家庭购车比较任务。"""

        return {"final_answer": "当前步骤只负责编排家庭购车比较任务。"}

    def restricted_action(state: GraphState) -> dict:
        """受限动作分支：本步只有规划能力，不执行下单、贷款、付款等动作。"""

        return {"final_answer": "本步骤只制定比较计划，不能执行下单、贷款或付款。"}

    def supervisor(state: GraphState) -> dict:
        """监督节点：只盘点进度，不亲自调用模型或工具。"""

        # 用 set 做成员判断更直观：completed_items 中出现过的 id 就视为已完成。
        # Supervisor 的职责是“决定下一步是否还要派工”，不是替 specialist 做具体工作。
        pending = [item for item in state["work_items"] if item["id"] not in set(state["completed_items"])]
        # trace 记录的是观察结果；它不会改变调度决定，真正的决定由紧接着的 dispatch 完成。
        return {"trace": [{"node": "supervisor", "pending": len(pending)}]}

    def dispatch(state: GraphState) -> str:
        """条件边：还有未完成任务就回 specialist，否则进入汇总节点。"""

        # Step2 故意一次只派一个任务，方便观察顺序执行和循环收敛；Step5 才会一次返回多个 Send 并行派工。
        completed = set(state["completed_items"])
        # any(...) 只要找到一个未完成任务就返回 True；全部完成时才允许 fan-in 到 compose_context。
        return "specialist" if any(item["id"] not in completed for item in state["work_items"]) else "compose_context"

    def specialist(state: GraphState) -> dict:
        """执行一个任务的教学替身。

        本步为了专注学习循环，specialist 仍调用 LLM 说明“应查询什么”，并明确禁止输出未经查询的事实。
        Step4 会把这里替换成真实 web/SQL 适配器；因此本节点生成的 evidence 只能当作计划说明，不能当作真实资料。
        """

        # 找到第一个未完成项。结果写入 evidence，任务 id 写入 completed_items。
        completed = set(state["completed_items"])
        item = WorkItem.model_validate(next(x for x in state["work_items"] if x["id"] not in completed))
        started = time.perf_counter()
        # item.instruction 是 plan 针对当前数据源生成的聚焦指令；总问题和当前子任务一起交给模型，便于理解上下文。
        result = str(model.llm.invoke(
            f"家庭购车总任务：{state['question']}\n当前步骤：{item.instruction}\n"
            "只说明这一项应查询什么、需要哪些字段和完成标准；不要给出未查询的车型事实或数字。"
        ).content)
        # 统一包装成 Evidence，后面的 compose_context 不必知道 specialist 具体调用了什么。
        evidence: Evidence = {"source": item.source, "title": item.instruction,
                              "content": result, "reference": f"step02://{item.id}"}
        # completed_items 和 evidence 都是“追加型”字段，Reducer 会把本次单项结果累加到已有列表。
        return {"completed_items": [item.id], "evidence": [evidence],
                "trace": [{"node": "specialist", "task": item.id,
                           "duration_ms": round((time.perf_counter()-started)*1000)}]}

    def compose_context(state: GraphState) -> dict:
        """fan-in（汇入）节点：把所有 specialist 结果拼成一个生成 Prompt 可读的上下文。"""

        # 只有 dispatch 判断所有任务完成后，图才会到这里；因此这是本步循环的统一出口。
        context = "\n\n".join(f"[{i}] {item['content']}" for i, item in enumerate(state["evidence"], 1))
        # 给每段内容编号，后续答案更容易引用“第几条结果”；本步没有额外加入真实 URL。
        return {"context": context, "trace": [{"node": "compose_context", "items": len(state["evidence"])}]}

    def generate(state: GraphState) -> dict:
        """所有计划任务完成后生成最终说明。"""

        # generate 只消费整理后的 context，不参与任务调度；职责分离后每个节点更容易单独测试。
        return {"final_answer": model.generate(state["question"], "", state["context"], "")}

    # 构图分成两类语句：add_node 注册“做什么”，add_edge 描述“什么时候走到哪里”。
    graph = StateGraph(GraphState)
    # 用列表批量注册节点，减少重复代码；列表里的字符串必须和后面的边名完全一致。
    for name, node in [("intake", intake), ("route", route),
                       ("clarify", clarify), ("out_of_scope", out_of_scope),
                       ("restricted_action", restricted_action), ("plan", plan),
                       ("supervisor", supervisor), ("specialist", specialist),
                       ("compose_context", compose_context), ("generate", generate)]:
        graph.add_node(name, node)
    # 入口先清洗，再让模型路由；START/END 是 LangGraph 提供的特殊标记，不是自定义节点函数。
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "route")
    # after_route 返回的字符串必须能在这个映射中找到，否则图无法知道下一节点是谁。
    graph.add_conditional_edges("route", after_route,
                                {"clarify": "clarify", "out_of_scope": "out_of_scope",
                                 "restricted_action": "restricted_action",
                                 "plan": "plan", "generate": "generate"})
    # 这些分支已经得到最终提示，直接结束；它们不会绕进 specialist 循环。
    graph.add_edge("clarify", END)
    graph.add_edge("out_of_scope", END)
    graph.add_edge("restricted_action", END)
    # 正常主线：规划 → 监督 →（一个 specialist → 再监督）循环。
    graph.add_edge("plan", "supervisor")
    graph.add_conditional_edges("supervisor", dispatch,
                                {"specialist": "specialist", "compose_context": "compose_context"})
    # specialist 完成后回 Supervisor；这条回边就是 Plan-and-Execute 循环。
    graph.add_edge("specialist", "supervisor")
    graph.add_edge("compose_context", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def initial_state(question: str) -> GraphState:
    """创建一次全新的运行输入。

    列表字段必须从空列表开始，因为后续节点会通过 Reducer 追加任务结果和 trace；
    如果省略它们，节点读取或合并状态时就可能出现 KeyError 或类型不一致。
    """

    return {"question": question, "route": {}, "work_items": [], "completed_items": [],
            "evidence": [], "context": "", "final_answer": "", "trace": []}


def run(question: str, stream_mode: str = "updates",
        trace_path: str = "reports/day31_40_step02.jsonl") -> dict:
    """运行图，同时把每次流式输出保存为 JSONL。

    JSONL 即“一行一个 JSON 对象”：即使运行中途有很多节点更新，也可以逐行查看，
    不必等到程序结束才知道图停在哪一步。
    """

    app = build_graph()
    # final 用于把 updates 模式下的多个增量拼回一个近似最终状态，便于函数返回给调用方。
    final = dict(initial_state(question))
    path = Path(trace_path)
    # mkdir(exist_ok=True) 让默认的 reports 目录不存在时也能直接运行。
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        # updates 看增量、values 看完整 State、messages 看模型流、debug 看底层调度。
        for chunk in app.stream(initial_state(question), stream_mode=stream_mode):
            # default=str 可以把某些非基础对象转成字符串，避免写报告时因序列化失败而中断运行。
            line = json.dumps(chunk, ensure_ascii=False, default=str)
            output.write(line + "\n")
            print(line)
            if stream_mode == "updates":
                # updates 的 chunk 通常按“节点名 → 本次返回值”组织，所以要遍历 values。
                for update in chunk.values():
                    if isinstance(update, dict):
                        final.update(update)
            elif stream_mode == "values" and isinstance(chunk, dict):
                # values 已经是完整 State，直接覆盖 final 比逐字段 update 更准确。
                final = chunk
    return final


if __name__ == "__main__":
    run("为预算 20 万、年行驶 1.5 万公里的四口之家，规划燃油、纯电和插混对比步骤")
