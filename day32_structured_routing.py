"""
Day 32 · 结构化输出路由：分支该走哪条，让 LLM 可靠地拍板
==========================================================
测试工程师转 AI 应用开发  ← 补生产缺口#3（承接 Day31，垫 Day33/Day39）

Day39 的 Supervisor 用关键词路由：last.content 里有没有 "RESEARCH"、"WRITING"…
问题：模型是自由文本，多说一句"我建议先 RESEARCH 再 WRITING"，你的 `in` 就同时命中，
路由乱套。生产里这种"用字符串匹配猜模型意图"是脆弱来源 top1。

正解：**结构化输出**。用 PydanticOutputParser 注入格式指令 + 后解析，逼模型只返回
一个受约束的值（枚举 / JSON），代码拿到的是确定字段，而不是要去解析的自由文本。
注意：DeepSeek 不支持 with_structured_output 的 json_schema 模式，
Parser 方案兼容任意模型，是更普适的做法。

本节两层：
【一】枚举路由：定义一个"下一步只能是这几个值"的 schema，模型必须从里面选一个。
    路由函数直接读字段，不再 in 关键字——稳定、可测、可断言。
【二】意图分类分流：客服场景，先把用户问题分类（查询/投诉/闲聊），再分派到不同处理节点。
    这就是 Day38 Text2SQL、RAG、闲聊怎么"按问题类型选工具"的通用做法。

对比：关键词路由=省 token 但脆；结构化路由=多一次约束但稳。生产选稳。

衔接：Day31 让节点稳；这里让"选哪条路"稳；Day33 规划、Day39 多 Agent 都靠它路由。
==========================================================
"""

import os
from typing import Literal, TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0.0, model: str = "deepseek-chat", **kwargs):
    """DeepSeek 对话模型（OpenAI 兼容）。temperature=0 → 输出可复现。"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temperature,
        **kwargs,
    )


# ============================================================
# 【一】枚举路由：模型只能从固定选项里选一个（对比 Day39 关键词）
# ============================================================
class RouteDecision(BaseModel):
    """强约束：next 只能是这四个值之一，模型没法自由发挥。"""
    next: Literal["research", "writing", "review", "finish"] = Field(
        description="根据当前进度，决定下一步交给哪个专家；任务完成则 finish"
    )
    reason: str = Field(description="一句话说明为什么这样路由（便于观测/复盘）")


class FlowState(TypedDict):
    task: str
    step_log: list
    done: bool
    _next: str  # supervisor 决策结果，route() 依赖此字段分流


def supervisor(state: FlowState) -> dict:
    """用 PydanticOutputParser 让模型返回结构化决策，而不是自由文本。
    注意：DeepSeek 不支持 with_structured_output（json_schema 模式），
    改用 parser 注入格式指令 + 后解析，兼容任意模型。"""
    parser = PydanticOutputParser(pydantic_object=RouteDecision)
    llm = get_llm(temperature=0)
    sys = SystemMessage(content=(
        "你是工作流主管。已完成步骤见下。请决定下一步：research/writing/review/finish。"
        f"\n已完成：{state['step_log']}"
        f"\n\n{parser.get_format_instructions()}"
    ))
    raw = llm.invoke([sys, HumanMessage(content=state["task"])])
    decision: RouteDecision = parser.parse(raw.content)
    print(f"  [supervisor] 决策 next={decision.next}  理由={decision.reason}")
    return {"step_log": state["step_log"] + [f"supervisor→{decision.next}"],
            "done": decision.next == "finish",
            # 把结构化结果暂存，供路由函数读取（确定字段，无需解析文本）
            "_next": decision.next}


def route(state: FlowState) -> str:
    """路由函数直接读结构化字段——对比 Day39 的 'if "RESEARCH" in text'，这里零歧义。"""
    return END if state.get("done") else state["_next"]


def make_expert(name: str):
    def expert(state: FlowState) -> dict:
        print(f"  [{name}] 处理中…")
        return {"step_log": state["step_log"] + [f"{name} 完成"]}
    return expert


def build_structured_supervisor():
    g = StateGraph(FlowState)
    g.add_node("supervisor", supervisor)
    for n in ["research", "writing", "review"]:
        g.add_node(n, make_expert(n))
    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", route, {
        "research": "research", "writing": "writing", "review": "review", END: END,
    })
    for n in ["research", "writing", "review"]:
        g.add_edge(n, "supervisor")   # 专家干完回主管，主管再结构化决策下一步
    return g.compile()


# ============================================================
# 【二】意图分类分流：按问题类型选处理路径（RAG/SQL/闲聊 通用骨架）
# ============================================================
class Intent(BaseModel):
    """把用户问题分到确定的类别，代码据此分派。"""
    category: Literal["knowledge", "data_query", "chitchat"] = Field(
        description="knowledge=查文档知识, data_query=查结构化数据/数字, chitchat=闲聊"
    )


class ChatState(TypedDict):
    question: str
    category: str
    answer: str


def classify(state: ChatState) -> dict:
    parser = PydanticOutputParser(pydantic_object=Intent)
    llm = get_llm(temperature=0)
    intent: Intent = parser.parse(llm.invoke([
        SystemMessage(content="判断用户问题类型，只输出类别。\n" + parser.get_format_instructions()),
        HumanMessage(content=state["question"]),
    ]).content)
    print(f"  [classify] 「{state['question']}」→ {intent.category}")
    return {"category": intent.category}


def route_intent(state: ChatState) -> str:
    return state["category"]


def build_intent_router():
    g = StateGraph(ChatState)
    g.add_node("classify", classify)
    # 三个处理分支（真实项目里分别接 RAG / Text2SQL(Day38) / 普通对话）
    g.add_node("knowledge", lambda s: {"answer": "[走 RAG 检索文档] " + s["question"]})
    g.add_node("data_query", lambda s: {"answer": "[走 Text2SQL 查库] " + s["question"]})
    g.add_node("chitchat", lambda s: {"answer": "[普通对话] 你好呀～"})
    g.add_edge(START, "classify")
    g.add_conditional_edges("classify", route_intent, {
        "knowledge": "knowledge", "data_query": "data_query", "chitchat": "chitchat",
    })
    for n in ["knowledge", "data_query", "chitchat"]:
        g.add_edge(n, END)
    return g.compile()


if __name__ == "__main__":
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("未配置 DEEPSEEK_API_KEY，本文件需真实 LLM 演示结构化输出，跳过运行。")
        raise SystemExit(0)

    print("===== 【一】结构化路由的 Supervisor（对比 Day39 关键词路由）=====")
    app = build_structured_supervisor()
    out = app.invoke({"task": "写一篇 Python 装饰器短文", "step_log": [], "done": False, "_next": ""},
                     {"recursion_limit": 12})
    print("  流程轨迹：", out["step_log"])

    print("\n===== 【二】意图分类分流（RAG/SQL/闲聊 通用骨架）=====")
    router = build_intent_router()
    for q in ["RAG 的原理是什么？", "示例科技 2025Q2 利润多少？", "在吗，聊聊天"]:
        r = router.invoke({"question": q, "category": "", "answer": ""})
        print("  →", r["answer"])


# ----------------------------------------------------------
# 小结：
# - 路由不要用"字符串 in 自由文本"猜意图（Day39 的做法脆弱）；用结构化输出
#   把模型输出约束成枚举/JSON，代码读到的是确定字段。
# - PydanticOutputParser 兼容任意模型（DeepSeek 等不支持 with_structured_output 的模型），
#   通过 format_instructions 注入到 prompt + parse() 后解析，效果等价。
# - Literal 枚举 = 最省事的强约束：模型只能从给定选项里选，路由函数零歧义、可断言。
# - 意图分类分流是通用骨架：一个 classify 节点决定走 RAG / Text2SQL / 闲聊。
# - 代价：多一次 LLM 调用/约束。换来的是可测、可复现、不跑偏——生产值这个价。
#
# 面试话术：
#   "多分支路由我不用关键词匹配模型的自由文本，那不稳定；我用结构化输出把决策约束成枚举，
#    路由函数直接读字段，既可单元测试（给定输入断言走哪条），也不会因模型多说一句就跑偏。
#    如果模型不支持原生 structured output（如 DeepSeek），我用 PydanticOutputParser
#    把 schema 注入 prompt，再 parse 文本——效果一样，兼容性更好。"
#
# 动手练习：把 Day39 的 route_by_supervisor 换成本节的 RouteDecision 结构化版，
#          再写个 pytest：喂固定 state，断言路由到预期节点（呼应 Day48 回归测试）。
# ----------------------------------------------------------
