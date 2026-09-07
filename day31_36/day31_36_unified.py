"""
Day 31~36 统一版：一张图，六天能力全开
================================================================
这是 day31_36_merged_agent.py 的"彻底统一"版：不靠开关，把 Day31~36
所有生产能力直接平铺进同一张基础图，跑一次就能看到全部在起作用。

    基础环：  START → decide → run_tool → END
    （Day33 的 Plan-and-Execute 是另一种范式，仍作为独立变体放文件末尾，
      不混进主环——混进去会破坏 ReAct 环的教学清晰度）

主环叠加的能力（全部默认生效）：
    Day31 容错   decide 调 LLM 失败 → 降级消息不崩；run_tool 工具失败 → 降级 ToolMessage
    Day32 路由   decide 用 PydanticOutputParser 结构化输出 next 枚举（确定性分支）
    Day34 可观测 stream 每步轨迹 + 落盘 JSONL
    Day35 持久化 compile(checkpointer) 按 thread_id 存快照
    Day36 HITL   run_tool 执行前 interrupt 等人确认（HIGH_RISK_TOOLS 命中才拦）

运行：
    .venv\Scripts\python.exe day31_36_unified.py
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
from langchain_core.output_parsers import PydanticOutputParser
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
# 自定义 State（延续 day30 风格）
# ============================================================
class ReactState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    step: Annotated[list[str], operator.add]
    finished: bool
    next: str                      # Day32 结构化路由结果（use_tool / done）


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
# 极简工具（延续 day30 最终版）
# ============================================================
_WEATHER_DB = {
    "北京": "晴，25℃", "上海": "多云，28℃",
    "广州": "雷阵雨，30℃", "深圳": "阴，29℃",
}

# Day36：标记高风险工具。命中才在 run_tool 前 interrupt 等人。
# 演示用：把 get_weather 临时标成高风险，就能看到 HITL 生效。
HIGH_RISK_TOOLS = {"get_weather"}

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
# Day32 结构化路由 schema（主环直接用它做确定性分支）
# ============================================================
class RouteDecision(BaseModel):
    """Day32：让模型用枚举明确决定下一步，而不是靠 tools_condition 隐式判断。"""
    next: Literal["use_tool", "done"] = Field(description="use_tool=调工具, done=直接回答")
    reason: str = Field(description="一句话说明为什么这样路由")


# ============================================================
# decide 节点：Day31 容错 + Day32 结构化路由 + Day34 轨迹
# ============================================================
_ROUTE_PARSER = PydanticOutputParser(pydantic_object=RouteDecision)
_ROUTE_SYS = SystemMessage(content=(
    "你是路由决策器。根据对话历史，决定下一步：use_tool（需要调用工具）或 done（直接回答）。"
    + _ROUTE_PARSER.get_format_instructions()
))


def decide(state: ReactState) -> dict:
    """基础环的 decide：让 LLM 决定下一步，并用结构化输出确定分支。"""
    print(f"\n[decide] 进入：当前 {len(state['messages'])} 条消息")

    # —— Day31 容错：LLM 调用失败不崩图 ——
    try:
        # 真实 ReAct 用 llm_with_tools，这里演示"结构化路由"时用普通 llm + parser
        response: AIMessage = llm_with_tools.invoke(state["messages"])
    except Exception as e:
        print(f"  [decide] LLM 失败：{type(e).__name__}，降级")
        response = AIMessage(content="（LLM 暂不可用，请稍后重试）")
        return {"messages": [response], "step": ["decide"], "finished": True, "next": "done"}

    # —— Day32 结构化路由：若有 tool_calls 直接走工具；否则用枚举确认 done ——
    if getattr(response, "tool_calls", None):
        nxt = "use_tool"
        reason = "模型要求调用工具"
    else:
        # 无 tool_calls → 用 RouteDecision 明确表达"done"，确定性更强
        try:
            decision = _ROUTE_PARSER.parse(llm_with_tools.invoke(
                [_ROUTE_SYS] + list(state["messages"]) + [response]
            ).content)
            nxt, reason = decision.next, decision.reason
        except Exception:
            nxt, reason = "done", "模型已直接回答"
    print(f"  [decide] 路由 → {nxt}（{reason}）")

    return {
        "messages": [response],
        "step": ["decide"],
        "finished": nxt == "done",
        "next": nxt,
    }


def route_decide(state: ReactState) -> str:
    """Day32 确定性分支：读 state['next'] 字段，零歧义。"""
    return state["next"] if state["next"] == "use_tool" else END


# ============================================================
# run_tool 节点：Day31 超时/错误 + Day36 HITL
# ============================================================
def run_tool(state: ReactState) -> dict:
    """基础环的 run_tool：执行工具，结果回灌 messages。"""
    last_ai = state["messages"][-1]
    calls = last_ai.tool_calls
    print(f"[run_tool] 进入：执行 {len(calls)} 个工具调用")

    # —— Day36 HITL：命中高风险工具 → interrupt 等人确认 ——
    if any(c["name"] in HIGH_RISK_TOOLS for c in calls):
        decision = interrupt({
            "action": "run_tool",
            "tools": [c["name"] for c in calls],
            "ask": "确认执行这些工具吗？(yes/no)",
        })
        if str(decision).lower() != "yes":
            print("  [run_tool] 用户取消")
            return {"messages": [ToolMessage(content="（用户取消）", tool_call_id=calls[0]["id"])],
                    "step": ["run_tool"], "next": "done"}

    tool_messages = []
    for call in calls:
        # —— Day31 超时/错误处理：工具失败给降级 ToolMessage 不崩 ——
        try:
            result = TOOL_MAP[call["name"]].invoke(call["args"])
        except Exception as e:
            print(f"  [run_tool] 工具 {call['name']} 失败：{type(e).__name__}，降级")
            result = f"（工具 {call['name']} 暂不可用）"
        tool_messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
        print(f"         → {call['name']}({call['args']}) = {str(result)[:30]}")
        # 高风险工具被人确认执行过，下一轮不再拦（演示简单化：清空标记）
        HIGH_RISK_TOOLS.discard(call["name"])

    return {"messages": tool_messages, "step": ["run_tool"], "next": "use_tool"}


# ============================================================
# 构建主环（六天能力全开）
# ============================================================
def build_unified_agent():
    g = StateGraph(ReactState)
    g.add_node("decide", decide)
    g.add_node("run_tool", run_tool)
    g.add_edge(START, "decide")
    g.add_conditional_edges("decide", route_decide, {"use_tool": "run_tool", END: END})
    g.add_edge("run_tool", "decide")
    # —— Day35 持久化 ——
    return g.compile(checkpointer=InMemorySaver())


# ============================================================
# Day34 可观测：stream 轨迹 + 落盘
# ============================================================
def run_agent(question: str, trace_path: str = "reports/day31_36_unified_trace.jsonl"):
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("请先设置 DEEPSEEK_API_KEY 环境变量。")
        return

    app = build_unified_agent()
    cfg = {"configurable": {"thread_id": "demo"}, "recursion_limit": 20}
    initial = {"messages": [HumanMessage(content=question)], "step": [],
              "finished": False, "next": ""}

    print(f"===== 统一版 · 问题：{question} =====")
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
    print(f"\n轨迹已落盘：{trace_path}；finished={final['finished']}")


if __name__ == "__main__":
    # 跑这个就能看到 Day31(容错)/Day32(结构化路由)/Day34(轨迹)/Day35(持久化)/Day36(HITL) 同时生效
    run_agent("北京和上海，哪个更热？")
