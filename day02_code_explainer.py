import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """你是代码讲师，用简洁中文解释代码。
输出格式：
1. 一句话总结这段代码做什么
2. 逐行解释关键部分
3. 有没有潜在问题"""),
    ("human", "请解释这段代码：\n```\n{code}\n```")
])

chain = prompt | llm | StrOutputParser()

code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

print(chain.invoke({"code": code}))
