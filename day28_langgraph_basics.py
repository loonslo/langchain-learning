"""
Day 28 · LangGraph 入门（下）：分支与循环 + 对比手写循环
==========================================================
测试工程师转 AI 应用开发  ← 阶段3 Agent（拆自原 Day28 下半，承接 Day27）

Day27 搭了最小【线性图】，但那和 LCEL 没区别。图真正的价值今天才登场：
【一】分支与循环：conditional_edges 按 state 决定下一步走哪条边；
    把条件边指回前面的节点就形成循环，用 recursion_limit 防死循环。
【二】对比手写循环：用 LangGraph 重写 Day05/Day10 的手写 while 工具循环，
    看清"框架到底替我做了什么"（这层封装叫 harness）。

一句话：分支/循环/状态，才是"要用图而不是 LCEL"的理由。

衔接：Day27 是线性图基础；本文件加分支/循环；Day29 讲 state 合并(reducer)；
      Day30 加工具调用做成 ReAct Agent；Day39 升级到多 Agent（Supervisor）。
==========================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError
from langchain_core.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()   # 读 .env 里的 DEEPSEEK_API_KEY


# —— 内联 LLM 工厂：本文件自包含，不依赖 common.py，方便单独阅读 ——
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
# 【一】分支与循环：conditional_edges + recursion_limit
# ============================================================
class LoopState(TypedDict):
    quality: int   # 当前质量分
    rounds: int    # 已打磨轮数


def improve(state: LoopState) -> dict:
    """每轮质量 +1，轮数 +1。"""
    q, r = state["quality"] + 1, state["rounds"] + 1
    print(f"  [improve] 第{r}轮，质量 {q}")
    return {"quality": q, "rounds": r}


def route(state: LoopState) -> str:
    """条件函数：返回的字符串决定走哪条边。"""
    return "good_enough" if state["quality"] >= 5 else "keep_going"


def build_loop():
    g = StateGraph(LoopState)
    g.add_node("improve", improve)
    g.add_edge(START, "improve")
    g.add_conditional_edges("improve", route, {
        "keep_going": "improve",   # 不达标 → 回到自己，形成循环
        "good_enough": END,        # 达标 → 结束
    })
    return g.compile()


# ============================================================
# 【二】对比手写循环：LangGraph 重写工具调用 + 对比表
# ============================================================
@tool
def add(a: int, b: int) -> int:
    """计算 a + b。"""
    return a + b


TOOLS = [add]


def build_agent():
    llm = get_llm(temperature=0).bind_tools(TOOLS)

    def agent(state: MessagesState) -> dict:
        return {"messages": [llm.invoke(state["messages"])]}

    g = StateGraph(MessagesState)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)   # 有 tool_calls 就去 tools，否则结束
    g.add_edge("tools", "agent")                        # 工具结果回灌，循环
    return g.compile(checkpointer=InMemorySaver())       # 挂 checkpointer = 多轮记忆


COMPARISON = """
| 关注点            | 手写循环（Day05/Day10）          | LangGraph（本文件）              |
|------------------|----------------------------------|----------------------------------|
| 判断要不要调工具  | 自己解析 tool_calls + if 判断     | tools_condition 内置             |
| 执行工具+回灌结果 | 自己拼 ToolMessage 塞回 messages  | ToolNode 自动                    |
| 循环控制          | 自己 while + 自己防死循环         | 图的边 + recursion_limit         |
| 多轮记忆          | 自己维护 messages 列表            | checkpointer 按 thread_id 自动   |
| 中断/恢复/HITL    | 几乎没法做                        | interrupt + checkpointer 内置    |
结论：框架替我包掉的 = 工具解析、循环、记忆、中断恢复——这层就是 harness。
"""


if __name__ == "__main__":
    print("===== 【一】分支与循环 + 防死循环 =====")
    loop = build_loop()
    print("正常循环到达标：", loop.invoke({"quality": 0, "rounds": 0}))
    try:
        # 从 0 分到 5 分要 5 轮，但只允许 4 步 → 触发上限保护
        loop.invoke({"quality": 0, "rounds": 0}, {"recursion_limit": 4})
    except GraphRecursionError as e:
        print(f"  已被 recursion_limit 拦截（防死循环生效）：{type(e).__name__}")

    print("\n===== 【二】LangGraph 工具 Agent（带记忆）+ 对比 =====")
    app = build_agent()
    cfg = {"configurable": {"thread_id": "t1"}}
    r1 = app.invoke({"messages": [("user", "帮我算 18 加 24")]}, cfg)
    print("第1轮：", r1["messages"][-1].content)
    r2 = app.invoke({"messages": [("user", "再加 100 呢")]}, cfg)   # 靠记忆理解"再加"
    print("第2轮（带记忆）：", r2["messages"][-1].content)
    print(COMPARISON)


# ----------------------------------------------------------
# 小结：
# - conditional_edges：用路由函数按 state 决定下一跳，是分支/循环的核心；
#   循环 = 把条件边指回前面的节点，靠退出条件停下。
# - recursion_limit：步数安全阀，超了抛 GraphRecursionError。生产 Agent 必配。
# - 对比手写循环：框架替你包掉工具解析、循环、记忆、中断恢复——这就是 harness 层。
# - 承接 Day27：线性图无所谓用不用图；分支/循环/状态才是"必须用图"的理由。
# - 路由目前用字符串返回；生产里更稳的做法是结构化输出路由（见 Day32）。
# ----------------------------------------------------------
