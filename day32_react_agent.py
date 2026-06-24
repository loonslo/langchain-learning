"""
Day 32 · ReAct：用 create_react_agent 一行搭出来 + 讲清思想
==========================================================
测试工程师转 AI 应用开发

Day25 手搭了 agent↔tools 循环。这套"边想边做"的范式有个名字：ReAct
（Reasoning + Acting）：模型先想一步该干嘛 → 调工具行动 → 看结果（observation）
→ 再想下一步……直到能回答。day03/05 其实已是它的雏形。

LangGraph 把这套封装成 create_react_agent，一行就得到一个 ReAct Agent，
内部就是 Day25 那张图。生产里常直接用它，省得每次手搭。

也顺带认识其他规划范式（只【了解】，会聊即可）：
- Plan-and-Execute：先把整个计划列出来再逐步执行（Day27 动手）
- Reflexion：失败后自我反思、带教训重试
- ReWOO：先一次性规划好所有工具调用，减少 LLM 往返
- Tree of Thoughts：把多条思路当树来搜索，挑最好的
==========================================================
"""

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from common import get_llm


@tool
def add(a: int, b: int) -> int:
    """两个整数相加。"""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """两个整数相乘。"""
    return a * b


@tool
def get_weather(city: str) -> str:
    """查询城市天气（演示假数据）。"""
    return f"{city}今天多云，22℃"


if __name__ == "__main__":
    agent = create_react_agent(
        get_llm(temperature=0),
        tools=[add, multiply, get_weather],
        prompt="你是一个会用工具的助手。需要计算或查询时调用合适的工具，最后用中文回答。",
    )

    # 故意问需要连续两步的题，观察 ReAct 的"想→做→再想"
    q = "先算 3 乘以 4，再把结果加上 10，等于多少？"
    print(f"问：{q}\n")
    result = agent.invoke({"messages": [("user", q)]})

    # 打印完整轨迹：能看到模型怎么一步步推理 + 调工具
    for m in result["messages"]:
        role = type(m).__name__
        tc = getattr(m, "tool_calls", None)
        if tc:
            print(f"[{role}] 调用工具：{[(c['name'], c['args']) for c in tc]}")
        elif m.content:
            print(f"[{role}] {m.content}")


# ----------------------------------------------------------
# 小结：
# - ReAct = Reasoning + Acting：想一步→调工具→看结果→再想，循环到能答。
# - create_react_agent 一行得到 ReAct Agent，内部就是 Day25 的 agent↔tools 图。
# - 何时手搭 vs 用现成：要自定义节点/分支/审批就手搭（Day27/30）；标准工具循环直接用它。
#
# 面试常问：ReAct 和 Plan-and-Execute 区别？
#   ReAct 走一步看一步，灵活但步数多、易跑偏；
#   Plan-Execute 先规划全程再执行，可控、省 LLM 往返，但计划错了全错。
#
# 动手练习：把 prompt 去掉，看模型还会不会主动调工具；再加一个查不到的城市观察反应。
# ----------------------------------------------------------
