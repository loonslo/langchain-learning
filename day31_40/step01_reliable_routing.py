"""Step 1 / Day31-32：先学会让节点稳定、让条件边可靠。

【这个文件是什么】
它是 Day31-40 系列里最精简的一张图，专门用来讲清楚两个基础概念：
  1. 节点（node）要稳定：调用 LLM / 外部工具时可能失败，要能重试、要能优雅降级。
  2. 条件边（conditional edge）要可靠：模型不要直接输出「下一步去哪」这种自由文本，
     而是输出一个结构化对象（RouteDecision），由我们自己的 Python 代码去决定走哪条边。
这样图的走向是「确定性」的，可测试、可预测，不会漂移。

【业务背景】
整张图的业务问题固定为「家庭买车」（调查车型、比较、估算成本）。本步回答两个核心问题：
  - 这个请求能不能执行？（范围检查、缺信息检查、是否需要人工审批）
  - 模型怎样可靠地决定下一条边？（读 RouteDecision 字段，而不是解析模型说的话）

【阅读顺序建议（新人必看）】
  1) GraphState        —— 节点之间唯一共享的数据结构
  2) ModelGateway      —— 模型调用的抽象接口（便于测试时替换成假模型）
  3) reliable_lookup   —— 工具调用如何重试 / 降级
  4) build_graph 里的各节点函数：intake → route → choose → (clarify/out_of_scope/...)
  5) 文件末尾的连边（add_edge / add_conditional_edges）

【和同目录其他文件的关系】
  - production_graph.py 是本系列「完整版」主图（含 SQL、MCP、质量门、人工审批等）。
  - adapters.py 封装真实 I/O（Tavily 搜索、SQLite、MCP），本文件只用到其中的搜索适配器。
  - 本文件刻意删掉完整版的大部分逻辑，只保留「路由 + 可靠调用」这条主线，方便入门。

【怎么跑起来】
  - 需要真实联网：在 .env 里配置 DEEPSEEK_API_KEY，安装 tavily-python 并配置 TAVILY_API_KEY，
    然后直接 `python step01_reliable_routing.py`。
  - 不想连真实服务：把 `build_graph()` 换成 `build_graph(model=假模型, evidence_adapter=假适配器)`，
    实现 ModelGateway / EvidenceAdapter 两个接口即可（见文件底部说明），无需任何 API key。
"""

from __future__ import annotations  # 允许在定义前/不立即求值的类型注解，方便声明递归或前置类型。

import time  # 重试时短暂等待，模拟生产中的退避。
from typing import Literal, Protocol, TypedDict  # Literal/Protocol/TypedDict 分别描述有限值、接口和 State 形状。

from langgraph.graph import END, START, StateGraph  # 用来定义图的起点、终点、节点和边。
from langgraph.types import RetryPolicy  # 给节点配置“哪些异常可以自动重试”。
# adapters.py 提供外部 I/O 封装与两类错误：
#   - TransientToolError：网络抖动、超时等「重试可能恢复」的错误
#   - PermanentToolError：缺 key、权限错误等「重试也不会好」的错误
#   - EvidenceAdapter：所有工具的统一接口，节点只认 collect(task) -> Evidence
#   - TavilySearchAdapter：真实联网搜索适配器（Day37 引入，这里直接用）
from .adapters import EvidenceAdapter, PermanentToolError, TavilySearchAdapter, TransientToolError
# production_graph.py 提供：
#   - DeepSeekGateway：真实模型调用网关（route / llm 等）
#   - Evidence：单条证据的数据结构（dict）
#   - RouteDecision：路由的结构化输出（Pydantic 模型），条件边只认它的字段
#   - retry_transient_llm_error：判断哪些 LLM 异常值得重试
from .production_graph import DeepSeekGateway, Evidence, RouteDecision, retry_transient_llm_error


class GraphState(TypedDict):
    """整张图在节点之间传递的数据包（State）。

    关键点：State 是节点之间**唯一**共享的数据。每个节点只返回自己**修改过的字段**，
    LangGraph 会自动把返回值合并回 State。节点之间不要靠全局变量偷偷传递业务结果，
    否则图就无法复现、无法测试。
    """
    # 用户原始问题（intake 节点会做去空格 / 长度校验）；这是整张图的输入起点。
    question: str
    # route 节点把模型的结构化路由结果（RouteDecision）存这里。
    # 条件边 choose() 只读取这个 dict 的字段来决定走哪条边，绝不解析自由文本。
    route: dict
    # evidence 是工具（如搜索）返回的原始结果列表；
    # context 是 compose_context 把 evidence 整理、编号后真正喂给生成模型的内容。
    evidence: list[Evidence]
    context: str
    # 最终给用户的答案；只有 clarify/out_of_scope/restricted_action/generate 会写入它。
    final_answer: str
    # 错误也进入 State（而不是只 print 一下就丢掉），这样调用方才能观测、审计、记录。
    errors: list[str]


class ModelGateway(Protocol):
    """模型调用的抽象接口（Protocol = 结构化约定，不强制继承）。

    为什么需要它：真正调用 DeepSeek 需要 API key，且结果有随机性，不方便做单元测试。
    把它抽成接口后，测试时可以传入一个「假模型」实现同样的方法，从而在不联网的情况下
    验证图的路由逻辑。本文件里 build_graph 默认用真实的 DeepSeekGateway。
    """
    # route 只负责“判断请求属于哪类情况”，不负责执行工具或写最终回答。
    def route(self, question: str, history_view: str) -> RouteDecision: ...
    @property
    def llm(self): ...  # generate 通过这个属性调用底层模型；测试替身也要提供同名属性。


def reliable_lookup(adapter: EvidenceAdapter, question: str,
                    max_attempts: int = 3) -> tuple[list[Evidence], list[str]]:
    """对真实搜索做有限重试；配置错误快速失败，绝不返回编造资料。

    返回两样东西：(证据列表, 错误信息列表)。即使失败也尽量返回「诚实降级」的证据，
    而不是编造内容——这是生产可靠性的底线。

    重试策略的核心区分：
      - 瞬时错误（TransientToolError / 超时 / 断连）：可能下一次就恢复，允许有限重试。
      - 永久错误（PermanentToolError，如缺 API key）：重试也不会好，直接抛出交给调用方。
    """
    # errors 不用来决定是否重试，它只是把失败历史带回 State，供日志和上层展示。
    errors: list[str] = []
    # range 从 1 开始更符合人类阅读的“第 1 次、第 2 次”；上限是包含在内的。
    for attempt in range(1, max_attempts + 1):
        try:
            # 适配器统一暴露 collect()，节点不必知道底层到底是 Tavily、HTTP 还是别的 SDK。
            return adapter.collect(question), errors
        # 超时/断连可能下一次就恢复，所以允许有限重试；每次间隔随次数线性增大。
        except (TransientToolError, TimeoutError, ConnectionError) as exc:
            errors.append(f"第 {attempt} 次瞬时失败：{type(exc).__name__}")
            if attempt < max_attempts:
                # 这里只等待很短时间用于教学；生产环境通常会使用更长、带抖动的指数退避。
                time.sleep(0.05 * attempt)
        # Key 缺失、权限错误等确定问题重试也不会恢复，直接交给调用方处理。
        except PermanentToolError:
            raise
    # 重试耗尽仍失败：返回一个标注 degraded 的占位证据，明确告诉下游「这次没拿到真实资料」，
    # 后续 generate 节点看到空 context 会如实说「不知道」，而不是胡编。
    # 返回值仍然符合 Evidence 结构，因此下游可以继续运行；warning 明确表示它不是实际搜索结果。
    return [{
        "source": "web",
        "title": "在线搜索暂不可用",
        "content": "真实搜索重试耗尽，本轮没有取得外部资料。",
        "reference": "unavailable://web", "warning": "degraded",
    }], errors


def build_graph(model: ModelGateway | None = None,
                evidence_adapter: EvidenceAdapter | None = None):
    """构建并返回编译后的图。

    参数注入（依赖倒置）：
      - model：默认 DeepSeekGateway（真实模型）；测试时可传入假模型。
      - evidence_adapter：默认 TavilySearchAdapter（真实搜索）；测试时可传入假适配器。
    这样「默认连真实服务，测试时换桩」，同一份图逻辑既能上线也能单测。
    """
    # 依赖注入的核心：生产运行使用真实服务，测试运行可以替换成完全可控的假对象。
    model = model or DeepSeekGateway()
    evidence_adapter = evidence_adapter or TavilySearchAdapter(max_results=3)

    def intake(state: GraphState) -> dict:
        """入口节点：清洗并校验问题。

        节点只返回自己修改的字段（这里只有 question），LangGraph 会把这份「增量」合并回 State。
        做两件事：
          1) 折叠多余空白，避免模型被奇怪空格干扰；
          2) 校验非空且长度上限，防止异常输入把后续节点搞崩。
        """
        # 节点只返回自己修改的字段，LangGraph 会把增量合并回 State。
        # 读取 State 中的 question；节点函数不接收额外的隐式参数。
        question = " ".join(state["question"].split())
        if not question or len(question) > 1000:
            raise ValueError("问题不能为空且不能超过 1000 字")
        return {"question": question}

    def route(state: GraphState) -> dict:
        """路由节点：让模型先「判断情况」，把结果存成结构化的 RouteDecision。

        【这个节点存在的意义 —— 新人重点看这里】
        如果不拆出这个节点，模型会直接生成最终答案，并且「自作主张」：
          该查资料时它凭记忆编、缺信息时它硬答、该走审批时它直接说"已下单"。
          这些分支你没法在代码里控制。
        拆出 route 后，把「判断情况」和「生成答案」分成两步：
          第一步（本节点）只让模型做一件事：打标签——在范围内吗？缺信息吗？
          需要审批吗？需要查 web 吗？结果是一份像表单一样的 RouteDecision。
          第二步由 choose() 条件边读这份表单的字段，确定性地决定走哪条边。
        核心收益：把「流程控制权」从模型手里收回到代码手里。模型只负责"判断"，
        代码负责"按判断执行"。图的走向变得可预测、可测试、不会漂移——
        这正是 Day31-32 整篇要教的东西。

        【实现细节】
        本节点没有直接写 model.llm.invoke(...)。它调用的是 ModelGateway 接口上的
        model.route(question, history_view) 方法——真正的模型调用发生在
        production_graph.py 的 DeepSeekGateway.route 内部（self.structured → self.llm.invoke）。
        封装在网关方法里，是为了让本节点只关心「拿决策、存 State」，
        测试时也可把 model 换成不联网的假实现。
        这里第二参传 ""，因为 Step1 还没学对话历史；后续完整版会传入历史视图。

        【RouteDecision 到底是什么 —— 新人重点看这里】
        它不是一句文字，而是一张模型必须照着填的「决策单」（在 production_graph.py
        定义为 Pydantic 模型），形状大致如下：
            intent: "public_info" | "family_data" | "calculation" | "chitchat"   # 意图，四选一
            sources: ["web"]                       # 需要哪些数据源
            in_scope: true                         # 是不是购车相关问题
            missing_information: []                # 缺哪些信息（字段名列表）
            requires_approval: false               # 要不要人工审批
            reason: "..."                          # 一句话理由
        举例：用户问"搜一下比亚迪汉落地价"，模型不会回"我去查查网"这种自由句，
        而是返回上面这种固定格式对象。差别在于：自由文本代码没法可靠判断走哪条边、
        今天说"查查"明天说"搜一下"容易跑偏；而有了这张单子，choose() 直接读
        decision.sources 里有没有 "web"、in_scope 是不是 false，就能 100% 确定地决定流程。
        一句话：让模型输出「机器能直接读的结构」，而不是「人能读懂的话」。
        """
        # RouteDecision 的 sources 是有限枚举；这是 Day32 的核心。
        # Step1 没有历史上下文，因此 history_view 传空字符串；统一签名为后续步骤留出扩展位。
        decision = model.route(state["question"], "")
        # model_dump 把 Pydantic 模型变成 dict；下一节点会用 model_validate 再检查一次结构。
        return {"route": decision.model_dump()}

    def choose(state: GraphState) -> str:
        """条件边函数：根据 RouteDecision 的字段，返回「下一步节点名」字符串。

        这是「可靠条件边」的关键：它只翻译结构化字段，不解析模型自由文本，
        也绝不在这里做 I/O（不查工具、不调模型）。纯 Python 逻辑，100% 可预测、可单测。
        返回值的字符串必须和下面 add_conditional_edges 注册的映射一一对应。
        """
        # 条件边只翻译结构化字段，不解析模型自由文本，也不在这里做 I/O。
        decision = RouteDecision.model_validate(state["route"])
        # 下面的 if 顺序就是业务优先级：先判断能不能处理，再判断是否敏感，再判断信息是否充足。
        # 1) 不在购车范围内 → 直接结束并说明。
        if not decision.in_scope:
            return "out_of_scope"
        # 2) 需要审批（如下单/贷款/付款）→ Step1 还不能做，安全终止（Step3 才学 HITL 恢复）。
        if decision.requires_approval:
            return "restricted_action"
        # 3) 缺必要信息 → 反问用户补充。
        if decision.missing_information:
            return "clarify"
        # 4) 需要联网资料 → 先走 specialist 取证据。
        if "web" in decision.sources:
            return "specialist"
        # 5) 其余（纯闲聊/直接可答）→ 直接生成。
        return "generate"

    def clarify(state: GraphState) -> dict:
        """缺信息分支：把模型指出的缺失字段拼成一句追问。"""
        # State 里是 dict，先还原成 RouteDecision，才能安全访问 missing_information。
        missing = RouteDecision.model_validate(state["route"]).missing_information
        return {"final_answer": "继续分析前，请补充：" + "、".join(missing) + "。"}

    def out_of_scope(state: GraphState) -> dict:
        """越界分支：明确告知只处理家庭购车相关问题。"""
        return {"final_answer": "当前助手只处理家庭购车调查、比较和成本问题。"}

    def restricted_action(state: GraphState) -> dict:
        """受限动作分支：Step1 尚未学习 HITL（人工介入），因此真实下单、贷款、付款请求先安全终止。

        为什么要「安全终止」而不是硬做？因为这是不可逆的敏感操作，本步还没引入审批恢复机制，
        宁可拒做也不能误执行；Step3 才会加入人工确认（interrupt / approval）再恢复流程。
        """
        # Step1 尚未学习 HITL，因此真实下单、贷款、付款请求先安全终止；Step3 再引入审批恢复。
        return {"final_answer": "当前阶段只能提供购车信息，不能执行下单、贷款或付款。"}

    def specialist(state: GraphState) -> dict:
        """取证节点：调用外部工具（这里是 Tavily 搜索）拿证据，并复用 reliable_lookup 的重试/降级。

        从 Step1 起就使用真实 URL（保留来源，便于可追溯）；Step4 完整版会增加 SQL 和更统一的适配器边界。
        """
        # 从 Step1 起就使用真实 URL；Step4 再增加 SQL 和统一的适配器边界。
        # 本节点不直接写重试逻辑，统一交给 reliable_lookup；这样工具调用策略只有一个实现。
        evidence, errors = reliable_lookup(evidence_adapter, state["question"])
        # errors 使用旧列表 + 新列表合并；Step1 没给 errors 配 Reducer，因此要由节点显式保留旧值。
        return {"evidence": evidence, "errors": state["errors"] + errors}

    def compose_context(state: GraphState) -> dict:
        """整理节点：把零散的 evidence 编号、拼接成一段统一格式的文本，存进 state["context"]。

        注意：本节点【不调用模型、也不做任何 I/O】，只是纯字符串格式化。
        真正的「把资料喂给模型」发生在后面的 generate 节点——它才会把 state["context"]
        拼进 prompt 并调用 model.llm.invoke(...)。本节点只是提前把资料整理好备用。

        evidence 是什么：specialist 节点调用搜索等工具返回的原始事实材料列表，
        每条是个 dict（含 content 正文、reference 来源等，详见 production_graph.py 的 Evidence）。
        不同工具返回格式不同，这里统一成 [1][2] 编号文本，好处是 generate 节点不必理解
        每种工具的原始格式，只看编号文本即可；[1][2] 也方便最终答案做引用溯源。
        """
        # 工具结果先标准化并编号，generate 不需要理解每种工具的返回格式。
        # enumerate(..., 1) 让引用编号从 [1] 开始，而不是 Python 默认的 [0]。
        return {"context": "\n\n".join(
            f"[{i}] {item['content']}\n来源：{item['reference']}"
            for i, item in enumerate(state["evidence"], 1)
        )}

    def generate(state: GraphState) -> dict:
        """生成节点：基于证据写最终答案。

        职责单一：只负责「基于证据写答案」，不在这里查工具、也不决定路由（那是 route/choose 的事）。
        提示词里强调「不代表已下单」「证据不足明确说不知道」，把安全边界写进指令。
        """
        # 生成节点只负责“基于证据写答案”，不在这里查询工具或决定路由。
        # context 为空时显式写“无”，让模型知道当前没有可引用资料，而不是误以为字段丢失。
        prompt = (f"问题：{state['question']}\n证据：{state['context'] or '无'}\n"
                  "只给家庭购车建议，不代表已经下单；证据不足时明确说不知道。用简洁中文回答。")
        # .content 是模型响应正文；str() 兼容不同模型 SDK 返回的可字符串化内容对象。
        return {"final_answer": str(model.llm.invoke(prompt).content)}

    # ---- 构图：先注册所有节点，再描述节点之间的边 ----
    # 心智模型：节点函数 = 「做什么」（业务逻辑）；边 = 「什么时候做 / 走哪条路」（流程控制）。
    graph = StateGraph(GraphState)
    # 给会调模型的节点挂上重试策略：只有 retry_transient_llm_error 判定为「瞬时」的异常才重试。
    llm_retry = RetryPolicy(max_attempts=3, retry_on=retry_transient_llm_error)
    # 普通节点按名字注册；route/generate 额外配置 LLM 瞬时错误的自动重试。
    graph.add_node("intake", intake)
    graph.add_node("route", route, retry_policy=llm_retry)
    graph.add_node("clarify", clarify)
    graph.add_node("out_of_scope", out_of_scope)
    graph.add_node("restricted_action", restricted_action)
    graph.add_node("specialist", specialist)
    graph.add_node("compose_context", compose_context)
    graph.add_node("generate", generate, retry_policy=llm_retry)
    # 线性入口：START → intake → route
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "route")
    # route 是这张小图唯一的分叉点：choose() 根据 RouteDecision 在 5 个分支里选一个。
    # 字典的左侧是 choose() 返回的字符串，右侧是对应要跳转的节点名。
    graph.add_conditional_edges("route", choose,
                                {"clarify": "clarify", "out_of_scope": "out_of_scope",
                                 "restricted_action": "restricted_action",
                                 "specialist": "specialist", "generate": "generate"})
    # 三个「直接结束」的分支：clarify / out_of_scope / restricted_action 都走向 END。
    graph.add_edge("clarify", END)
    graph.add_edge("out_of_scope", END)
    graph.add_edge("restricted_action", END)
    # 需要资料的分支：specialist 取证据 → compose_context 整理 → generate 作答 → END。
    graph.add_edge("specialist", "compose_context")
    graph.add_edge("compose_context", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def initial_state(question: str) -> GraphState:
    """构造图的初始输入。

    LangGraph 的 invoke 只接收「这次请求要带的数据」。空容器（route/evidence/errors 等）
    必须先初始化好，节点里才能安全地 `state["xxx"]` 取值或 `state["errors"] + ...` 拼接。
    """
    # route/evidence/context/final_answer/errors 都先放入明确的空值，节点就不用猜字段是否存在。
    return {"question": question, "route": {}, "evidence": [], "context": "",
            "final_answer": "", "errors": []}


if __name__ == "__main__":
    # 直接运行会用真实 DeepSeek + Tavily，需先配置 DEEPSEEK_API_KEY 和 TAVILY_API_KEY。
    # 若只想看图的走向、不想联网：把下面的 build_graph() 换成注入假模型/假适配器，
    # 例如 build_graph(model=FakeModel(), evidence_adapter=FakeAdapter())，
    # 只要 FakeModel 实现 route()/llm、FakeAdapter 实现 collect() 即可（见上方 ModelGateway / EvidenceAdapter）。
    result = build_graph().invoke(initial_state("搜索家庭购车总成本需要包含哪些费用，并保留来源"))
    print(result["final_answer"])
