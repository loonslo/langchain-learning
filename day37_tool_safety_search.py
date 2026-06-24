"""
Day 37 · 阶段3 综合项目（上）：搜索 + 总结 Agent
==========================================================
测试工程师转 AI 应用开发  ← 把 Agent 知识串成一个能用的东西

把前面学的串起来做个小项目：一个能联网搜索、再把结果总结成答案的 Agent。
本节先搭核心：搜索工具 + ReAct + 轨迹日志（每一步想了啥、调了啥都记下来）。
Day34 再加 human-in-the-loop 和状态持久化，做成端到端。

轨迹日志是测试背景的加分项——Agent 出错时，有完整轨迹才能定位"错在哪一步"。

依赖（可选）：pip install ddgs   # 真联网搜索；没装则自动用内置假数据，逻辑照样跑
==========================================================
"""

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from common import get_llm


# ---------- 搜索工具：装了 ddgs 就真搜，没装用假数据兜底（保证可跑）----------
@tool
def web_search(query: str) -> str:
    """联网搜索一个问题，返回若干条结果摘要。"""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=3))
        if hits:
            return "\n".join(f"- {h['title']}：{h['body'][:120]}" for h in hits)
    except Exception:
        pass
    # 兜底假数据：没网/没装依赖也能演示 Agent 流程
    return f"（离线示例结果）关于「{query}」：这是一条模拟搜索摘要，用于演示总结流程。"


def build_agent():
    return create_react_agent(
        get_llm(temperature=0),
        tools=[web_search],
        prompt="你是研究助理。遇到需要事实/最新信息的问题，先用 web_search 搜，再用中文总结成简洁回答，并说明依据。",
    )


def run(question: str):
    agent = build_agent()
    print(f"问题：{question}\n--- 执行轨迹 ---")
    trajectory = []
    # stream 出每一步，边跑边记轨迹（便于排错与展示）
    for chunk in agent.stream({"messages": [("user", question)]}, stream_mode="values"):
        msg = chunk["messages"][-1]
        role = type(msg).__name__
        tc = getattr(msg, "tool_calls", None)
        if tc:
            line = f"[{role}] 调用 {[(c['name'], c['args']) for c in tc]}"
        else:
            line = f"[{role}] {str(msg.content)[:100]}"
        trajectory.append(line)
        print(" ", line)
    print("--- 轨迹共", len(trajectory), "步 ---")
    return trajectory


if __name__ == "__main__":
    run("LangGraph 适合用来做什么？")


# ----------------------------------------------------------
# 小结：
# - 搜索+总结 Agent = 搜索工具 + ReAct 循环 + 让模型把结果总结成答案。
# - 用 agent.stream(stream_mode="values") 拿到每一步状态，记成轨迹日志。
# - 工具用"真依赖优先 + 假数据兜底"写法，保证没网/缺依赖时流程仍可跑通（利于测试）。
#
# 动手练习：给 web_search 加缓存（同一 query 不重复搜），对比有无缓存的调用次数。
# 下一步（Day34）：加 HITL（搜索前/给最终答案前让人确认）+ checkpoint 持久化。
# ----------------------------------------------------------
