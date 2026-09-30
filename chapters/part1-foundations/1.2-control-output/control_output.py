"""
章节 1.2 · 控制输出：随机性与流式
==========================================================
1.1 只问了一次。本章控制输出的形态：
1. temperature：回答的随机性（0 = 稳定，同一问题几乎每次一样；1 = 发散）
2. stream 流式输出：边生成边显示，而不是等全部生成完
3. 同一个问题在不同参数下对比，建立直观体感

评测、回归需要可复现，所以用 temperature=0；面向用户的界面常用流式输出改善等待体验。

前置：1.1
运行：python tools/run_chapter.py 1.2（调用真实模型，会产生少量费用）
输出：temperature 为 0 和 1 的两段回答，以及一段逐字打印的流式回答
==========================================================
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个创意作家"),
    ("human", "{question}"),
])
parser = StrOutputParser()


# ---------- 1. temperature 对比 ----------
# temperature 越低，模型越"保守稳定"，同一问题多次回答几乎一样；
# 越高越"天马行空"。下面同一个问题各问一次，感受差异。
for temp in [0.0, 1.0]:
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temp,          # 关键参数就在这里
    )
    chain = prompt | llm | parser
    print(f"\n========== temperature = {temp} ==========")
    print(chain.invoke({"question": "用一句话形容大海"}))


# ---------- 2. 流式输出（打字机效果）----------
# .stream() 返回一个生成器：模型边生成边吐字，而不是憋到最后一次性返回。
# 前端展示时用它，用户不用盯着空白干等。
print("\n\n========== 流式输出 ==========")
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
chain = prompt | llm | parser

for chunk in chain.stream({"question": "写一句鼓励正在转行学 AI 的人的话"}):
    print(chunk, end="", flush=True)   # end="" 不换行，flush=True 立刻刷新到屏幕
print()


# ----------------------------------------------------------
# 小结：
# - temperature=0  → 稳定、可复现，适合评测/抽取/分类
# - temperature 高 → 多样、有创意，适合文案/头脑风暴
# - .invoke() 一次性拿全部结果；.stream() 边生成边给，体验更好
#
# 动手练习：
# 1. 把 temperature=0 的那次连跑 3 遍，看是不是几乎一字不差
# 2. 给 stream 换一个长一点的问题，体会"流式"和"一次性"的区别
# ----------------------------------------------------------
