"""
Day 31~36 合并：一张生产级 ReAct 图
================================================================
把 Day31~36 六天的生产能力，全部织进同一张基础图：

    基础环（Day30）：  START → decide → run_tool → END

    Day31 容错重试     → decide / run_tool 节点内部加 try/except + fallback + 超时
    Day32 结构化路由   → decide 节点可选"用枚举输出决定走哪条边"（演示，单工具环下 tools_condition 已够）
    Day33 规划范式     → 可选开关：开启后变成 Plan-and-Execute 变体（planner 前置）
    Day34 可观测性     → 运行时 stream_mode="updates" 打印每步轨迹 + 结构化落盘
    Day35 持久化       → compile(checkpointer=...) 按 thread_id 存快照，支持中断恢复
    Day36 人工确认     → run_tool 之后可选 confirm 节点（interrupt 暂停等人）

设计原则（呼应你的要求）：
    - 主线就是基础环，所有能力都"长"在基础图上，不另起炉灶。
    - Day33 的 Plan-and-Execute 是另一种范式（先规划再执行），不是"叠加"在
      ReAct 上，所以作为独立 build 函数放在同文件，方便对比，而非硬塞进环。

运行：
    .venv\Scripts\python.exe day31_36_merged_agent.py
================================================================
"""

import os
import json
import time
from pathlib import Path
from typing import TypedDict, Annotated, Sequence, Literal
import operator

from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage,
)
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 自定义 State（延续 day30 风格，显式拆字段让"怎么走"看得见）
# ============================================================
class ReactState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]   # 对话+工具轨迹
    step: Annotated[list[str], operator.add]                   # 走过哪些节点（教学可视化）
    finished: bool                                             # 模型是否已决定回答
    # —— Day33 Plan-and-Execute 变体用 ——
    plan: list[str]                                            # 步骤清单
    cursor: int                                                # 当前执行到第几步


# ============================================================
# LLM 工厂
# ============================================================
def get_llm(temperature: float = 0.0, model: str = "deepseek-chat", **kwargs):
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temperature,
        **kwargs,
    )


# ============================================================
# 极简工具（延续 day30 最终版：不联网、确定性查表）
# 真实项目里这里是 Day38 的 Text2SQL / Day40 的 MCP 工具。
# ============================================================
_WEATHER_DB = {
    "北京": "晴，25℃", "上海": "多云，28℃",
    "广州": "雷阵雨，30℃", "深圳": "阴，29℃",
}

# 标记哪些工具是"高风险"（Day36 HITL 只对高风险工具拦截）
HIGH_RISK_TOOLS = set()   # get_weather 非高风险；演示时可在 run 里临时打开

@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。city 如 '北京' / '上海' / '广州' / '深圳'。"""
    if city not in _WEATHER_DB:
        return f"暂无 {city} 的天气数据"
    return f"{city}：{_WEATHER_DB[city]}"


TOOLS = [get_weather]
TOOL_MAP = {t.name: t for t in TOOLS}
llm_with_tools = get_llm(temperature=0).bind_tools(TOOLS)


# ============================================================
# Day32 结构化路由 schema（可选增强，演示用）
# ============================================================
class RouteDecision(BaseModel):
    """让模型用枚举明确决定下一步，而不是靠 tools_condition 隐式判断。"""
    next: Literal["use_tool", "done"] = Field(description="use_tool=调工具, done=直接回答")
    reason: str = Field(description="一句话说明为什么这样路由")


# ============================================================
# decide 节点：Day31 容错 + Day34 轨迹 + (可选) Day32 结构化路由
# ============================================================
def decide(state: ReactState) -> dict:
    """对应基础环的 decide：让 LLM 根据当前 messages 决定下一步。"""
    print(f"\n[decide] 进入：当前 {len(state['messages'])} 条消息")

    # —— Day31 容错：LLM 调用失败不崩图，返回降级消息 ——
    try:
        response: AIMessage = llm_with_tools.invoke(state["messages"])
    except Exception as e:
        print(f"  [decide] LLM 调用失败：{type(e).__name__}，降级回复")
        response = AIMessage(content="（LLM 暂时不可用，请检查网络后重试）")

    # —— Day32 结构化路由（可选演示）：若想让 decide 显式输出 next 枚举，
    #    可在此用 PydanticOutputParser 解析 response，把 next 存进 state["_next"]。
    #    单工具基础环下，tools_condition 已能靠 tool_calls 正确分支，这里不强制使用。
    #    parser = PydanticOutputParser(pydantic_object=RouteDecision)  # 见 day32

    # —— Day34 可观测：打印这一步在干什么 ——
    if getattr(response, "tool_calls", None):
        print(f"  [decide] 决定调工具：{[c['name'] for c in response.tool_calls]}")
    else:
        print(f"  [decide] 决定直接回答：{response.content[:40]}...")

    return {
        "messages": [response],
        "step": ["decide"],
        "finished": len(response.tool_calls) == 0,
    }


# ============================================================
# run_tool 节点：Day31 超时/错误处理 + Day36 HITL(可选)
# ============================================================
def run_tool(state: ReactState, use_hitl: bool = False) -> dict:
    """对应基础环的 run_tool：执行模型选中的工具，结果回灌 messages。"""
    last_ai = state["messages"][-1]
    print(f"[run_tool] 进入：执行 {len(last_ai.tool_calls)} 个工具调用")

    # —— Day36 HITL：高风险工具执行前，先 interrupt 等人确认 ——
    if use_hitl:
        # interrupt 会暂停整张图，等人 Command(resume="yes"/"no") 才继续
        decision = interrupt({
            "action": "run_tool",
            "tools": [c["name"] for c in last_ai.tool_calls],
            "ask": "确认执行这些工具吗？(yes/no)",
        })
        if str(decision).lower() != "yes":
            print("  [run_tool] 用户取消，不执行")
            return {"messages": [ToolMessage(content="（用户取消）", tool_call_id=last_ai.tool_calls[0]["id"])],
                    "step": ["run_tool"]}

    tool_messages = []
    for call in last_ai.tool_calls:
        name = call["name"]
        # —— Day31 超时/错误处理：工具调用包在 try 里，失败给降级 ToolMessage 不崩 ——
        try:
            result = TOOL_MAP[name].invoke(call["args"])   # 真实项目这里可能超时/报错
        except Exception as e:
            print(f"  [run_tool] 工具 {name} 失败：{type(e).__name__}，降级")
            result = f"（工具 {name} 暂不可用，请稍后重试）"
        tool_messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
        print(f"         → {name}({call['args']}) = {result[:30]}")

    return {"messages": tool_messages, "step": ["run_tool"]}


# ============================================================
# Day33 Plan-and-Execute 变体（另一种范式，不叠加在 ReAct 上）
# ============================================================
def planner(state: ReactState) -> dict:
    """把任务拆成有序步骤清单。"""
    prompt = ChatPromptTemplate.from_template(
        "把任务拆成 2-4 个有序步骤，每行一个，不要编号，不要解释：\n{task}"
    )
    text = (prompt | get_llm()).invoke({"task": state["messages"][-1].content})
    steps = [s.strip("-· ").strip() for s in str(text.content).splitlines() if s.strip()]
    print(f"[planner] 规划出 {len(steps)} 步：{steps}")
    return {"plan": steps, "cursor": 0, "step": ["planner"]}


def has_more(state: ReactState) -> str:
    return "more" if state["cursor"] < len(state["plan"]) else "done"


# ============================================================
# 构建：主线 = 基础环 + Day31/34/35/36；Day33 可选
# ============================================================
def build_production_agent(use_hitl: bool = False, use_planner: bool = False):
    """
    基础环（默认）：
        START → decide →(tools_condition)→ run_tool → decide → ... → END
    叠加能力：
        Day31   decide/run_tool 内部容错
        Day34   运行时 stream 轨迹（见 run_agent）
        Day35   compile(checkpointer) 持久化
        Day36   run_tool 后可选 confirm(interrupt)
    若 use_planner=True：变成 Plan-and-Execute 变体
        START → planner → decide → run_tool → decide → ... → has_more → END
    """
    # 用 lambda 把 use_hitl 透传给 run_tool（节点函数签名固定只收 state）
    def run_tool_node(state):
        return run_tool(state, use_hitl=use_hitl)

    g = StateGraph(ReactState)
    g.add_node("decide", decide)
    g.add_node("run_tool", run_tool_node)

    if use_planner:
        g.add_node("planner", planner)
        g.add_edge(START, "planner")
        g.add_edge("planner", "decide")
    else:
        g.add_edge(START, "decide")

    g.add_conditional_edges("decide", tools_condition)   # 有 tool_calls→run_tool，否则→END
    g.add_edge("run_tool", "decide")

    if use_planner:
        g.add_conditional_edges("decide",
                                lambda s: "more" if s["cursor"] < len(s["plan"]) else END,
                                {"more": "decide", END: END})

    # —— Day35 持久化：按 thread_id 存每步快照，支持中断恢复 ——
    return g.compile(checkpointer=InMemorySaver())


# ============================================================
# Day34 可观测：stream 轨迹 + 落盘 JSONL
# ============================================================
def run_agent(question: str, use_hitl: bool = False, use_planner: bool = False,
              trace_path: str = "reports/day31_36_trace.jsonl"):
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("请先设置 DEEPSEEK_API_KEY 环境变量。")
        return

    app = build_production_agent(use_hitl=use_hitl, use_planner=use_planner)
    cfg = {"configurable": {"thread_id": "demo"}, "recursion_limit": 20}
    initial = {"messages": [HumanMessage(content=question)], "step": [],
              "finished": False, "plan": [], "cursor": 0}

    print(f"===== 问题：{question} | HITL={use_hitl} | planner={use_planner} =====")
    Path(trace_path).parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(trace_path, "w", encoding="utf-8") as f:
        for chunk in app.stream(initial, cfg, stream_mode="updates"):
            for node, update in chunk.items():
                kinds = [type(m).__name__ for m in update.get("messages", [])]
                record = {"ts": round(time.time() - t0, 3), "node": node, "added": kinds}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"  ▼ [{node}] 追加了 {kinds}")

    final = app.invoke(initial, cfg)
    print(f"\n轨迹已落盘：{trace_path}；最终 finished={final['finished']}")


if __name__ == "__main__":
    # 1) 主线：基础环 + Day31/34/35（容错 + 可观测 + 持久化）
    run_agent("北京和上海，哪个更热？")

    # 2) 开 Day36 HITL：run_tool 前会 interrupt 等人确认（需手动输入 yes/no）
    # run_agent("北京天气怎么样？", use_hitl=True)

    # 3) Day33 变体：Plan-and-Execute（先规划再执行）
    # run_agent("帮我比较北京和上海的天气并总结", use_planner=True)
