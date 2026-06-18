"""
Day 1 · 第一次和大模型对话
==========================================================
测试工程师转 AI 应用开发

这一节你会学到：
1. 怎么用 LangChain 调用一个大模型（最简单的一次问答）
2. ChatPromptTemplate 是什么，system / human 两种角色各干嘛
3. LCEL 管道写法：prompt | llm | parser，这个 "|" 到底是什么意思

前置：把 DEEPSEEK_API_KEY 配到环境变量，或放进同目录 .env 文件
产出：跑通两种调用方式，看到模型回答
==========================================================
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 从 .env 读取密钥。好习惯：API key 绝不写进代码，避免上传 GitHub 时泄露
load_dotenv()

# 初始化模型。
# DeepSeek 兼容 OpenAI 的接口格式，所以直接用 ChatOpenAI，只要把 base_url 改成 DeepSeek 的地址。
# 想换成别的模型（如通义、Kimi），通常也是改 model + base_url 这两行。
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


# ---------- 方式一：最直接的一次调用 ----------
# llm.invoke(一句话) 把内容发给模型，返回一个"消息对象"，.content 才是文字
response = llm.invoke("用一句话解释什么是 RAG")
print("【方式一·直接调用】")
print(response.content)


# ---------- 方式二：Prompt 模板 + LCEL 管道（推荐，后面全用这个）----------
# ChatPromptTemplate：把"角色设定"和"用户问题"做成可复用的模板。
#   - system：给模型定身份、规则、口吻（用户看不到）
#   - human ：用户这一轮说的话；{question} 是占位符，调用时再填进去
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个 Python 专家，用简洁的中文回答"),
    ("human", "{question}"),
])

# StrOutputParser：把模型返回的消息对象，剥成纯字符串，方便直接打印/使用
parser = StrOutputParser()

# LCEL 管道："|" 表示"左边的输出，喂给右边当输入"，和 Linux 管道是一个意思。
#   prompt 填好模板 → llm 生成回答 → parser 取出纯文字
# 好处：每个零件都能单独替换（换模型、换解析器都不影响其它部分），链路一眼看懂。
chain = prompt | llm | parser

result = chain.invoke({"question": "什么是装饰器？"})
print("\n【方式二·模板 + LCEL】")
print(result)


# ----------------------------------------------------------
# 小结：
# - llm.invoke(文本)          适合临时问一句
# - prompt | llm | parser     适合做成可复用的处理链，是 LangChain 最核心的写法
#
# 动手练习：
# 1. 把 system 改成"你是一个资深测试工程师"，看回答风格怎么变
# 2. 把 {question} 换成你正在纠结的一个技术问题，跑一遍
# ----------------------------------------------------------
