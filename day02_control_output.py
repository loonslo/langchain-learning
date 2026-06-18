"""
Day 2 · 控制模型怎么"说话"
==========================================================
测试工程师转 AI 应用开发

Day1 学会了"问一次"。这一节学怎么控制输出的形态：
1. temperature：控制回答的随机性（0 = 稳定可复现，1 = 发散有创意）
2. stream 流式输出：像打字机一样一个字一个字蹦，而不是干等全部生成完
3. 同一个问题，不同参数下效果对比，建立直观体感

为什么测试转 AI 的人要重视这个？
  评测、回归这类场景要的是"可复现"，必须用 temperature=0；
  面向用户的产品则常用流式输出来改善体验。这是后面所有应用的基本功。
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
