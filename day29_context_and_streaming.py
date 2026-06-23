"""
Day 29 · 上下文管理（裁剪/摘要）+ streaming 流式
==========================================================
测试工程师转 AI 应用开发

两个真实场景必备能力：

1. 上下文管理：对话越长，messages 越多，迟早超出模型上下文窗口，还越来越贵。
   常见策略：只留最近 N 轮 + 把更早的压成一段摘要。这就是 2026 高频词
   "Context Engineering"。本节实现"保留最近 N 条 + 旧消息摘要"。

2. streaming：长回答让用户干等体验差。流式可以边生成边吐字，
   还能实时看到 Agent 每一步（调了哪个工具），便于观测。
==========================================================
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from common import get_llm

llm = get_llm(temperature=0)


# ============ 第一部分：上下文裁剪 + 摘要压缩 ============
def compress_history(messages: list, keep_recent: int = 2) -> list:
    """保留最近 keep_recent 条，更早的压成一条摘要 SystemMessage。"""
    if len(messages) <= keep_recent:
        return messages

    old, recent = messages[:-keep_recent], messages[-keep_recent:]
    text = "\n".join(f"{type(m).__name__}: {m.content}" for m in old)
    summary = (ChatPromptTemplate.from_template(
        "用一两句话概括下面这段对话历史，保留关键事实：\n{h}"
    ) | llm | StrOutputParser()).invoke({"h": text})

    print(f"  [压缩] {len(old)} 条旧消息 → 1 条摘要：{summary[:50]}...")
    return [SystemMessage(content=f"对话历史摘要：{summary}")] + recent


def demo_context():
    # 造一段较长的假历史
    history = [
        HumanMessage(content="我叫小王，在学 RAG"),
        AIMessage(content="好的小王，RAG 是检索增强生成"),
        HumanMessage(content="我之前是做测试的"),
        AIMessage(content="测试背景对 RAG 评测很有优势"),
        HumanMessage(content="那我现在叫什么名字？"),
    ]
    print("原始历史 5 条 → 压缩（保留最近 2 条 + 摘要）：")
    compressed = compress_history(history, keep_recent=2)
    print(f"  压缩后 {len(compressed)} 条")
    ans = llm.invoke(compressed).content   # 摘要里应保住"小王"，模型还能答对名字
    print("  问'我叫什么'，模型答：", ans[:50])


# ============ 第二部分：streaming 流式输出 ============
def demo_streaming():
    print("\n流式逐字输出（边生成边显示）：")
    chain = ChatPromptTemplate.from_template("用三句话介绍 {x}") | llm | StrOutputParser()
    for chunk in chain.stream({"x": "LangGraph"}):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    print("===== 1) 上下文裁剪 + 摘要 =====")
    demo_context()
    print("\n===== 2) streaming =====")
    demo_streaming()


# ----------------------------------------------------------
# 小结：
# - 上下文管理（Context Engineering）：留最近 N 轮 + 旧消息摘要，控制 token、不超窗口。
#   关键是"该留的事实别在摘要里丢"（如名字、关键决定）。
# - streaming：.stream() 边生成边返回；LangGraph 的 app.stream(..., stream_mode=...)
#   还能流式吐出每一步中间状态，既改善体验也利于观测。
#
# 动手练习：把 keep_recent 改成 1，看摘要还保不保得住"小王"这个名字。
# ----------------------------------------------------------
