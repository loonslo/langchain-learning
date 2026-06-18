"""
Day 3 · 结构化输出：从"一段文字"到"程序能直接用的数据"
==========================================================
测试工程师转 AI 应用开发

前两节模型返回的都是"一段话"，人看没问题，但程序不好用。
这一节让模型返回**结构化数据**（带字段的对象），比如：
    {summary: "...", issues: [...], score: 7}
这样就能 result.score 直接取值、写进数据库、做断言。

知识点：
1. 用 Pydantic 的 BaseModel 定义你想要的数据结构
2. llm.with_structured_output(模型) 让大模型按这个结构输出
3. 为什么它比"提示模型输出 JSON 再自己解析"更稳（底层走 function calling）

对测试转 AI 的人尤其重要：把模型输出变成结构化数据，是做"自动评测/断言"的前提。
==========================================================
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


# ---------- 例子一：代码审查，输出结构化结果 ----------
# 用 Pydantic 类描述"我想要什么字段、每个字段是什么类型"。
# Field 的 description 会被传给模型，等于在告诉它每个字段填什么。
class CodeReview(BaseModel):
    """代码审查结果"""
    summary: str = Field(description="一句话总结这段代码做什么")
    issues: list[str] = Field(description="潜在问题列表，没有就空列表")
    score: int = Field(description="代码质量分，1-10 的整数")


# with_structured_output：让模型直接吐出 CodeReview 对象。
# - 不用再写 JsonOutputParser，也不用手动塞"请按 JSON 格式输出"的说明
# - 底层走 function calling，比"让模型自己拼 JSON 再解析"稳得多，几乎不会解析失败
# - 返回的就是 CodeReview 对象，用 .summary / .score 取值（不是字典，不用 ["score"]）
# DeepSeek 兼容 OpenAI 的 function calling，显式指定 method 更稳妥。
structured_llm = llm.with_structured_output(CodeReview, method="function_calling")

prompt = ChatPromptTemplate.from_template("""
你是代码审查专家，审查以下代码并给出评价。
代码：{code}
""")

chain = prompt | structured_llm

result = chain.invoke({
    "code": """
    def get_user(id):
        sql = f"SELECT * FROM users WHERE id = {id}"
        return db.execute(sql)
    """
})

print("【代码审查】")
print("总结：", result.summary)
print("评分：", result.score)        # 直接当对象用，IDE 还能自动补全
print("问题：", result.issues)


# ---------- 例子二：情感分析，批量处理 ----------
class SentimentResult(BaseModel):
    """情感分析结果"""
    sentiment: str = Field(description="positive / negative / neutral 三选一")
    confidence: float = Field(description="置信度，0 到 1 之间的小数")
    keywords: list[str] = Field(description="触发该情感的关键词")


structured_llm2 = llm.with_structured_output(SentimentResult, method="function_calling")
prompt2 = ChatPromptTemplate.from_template("分析以下文本的情感倾向。\n文本：{text}")
chain2 = prompt2 | structured_llm2

texts = [
    "今天跑通了第一行 LangChain 代码，感觉还不错",
    "学了三天还是看不懂，太难了，想放弃",
    "就那样吧，也没什么特别的感受",
]

print("\n【情感分析】")
for text in texts:
    r = chain2.invoke({"text": text})
    print(f"文本：{text}")
    print(f"  情感：{r.sentiment}，置信度：{r.confidence}，关键词：{r.keywords}")


# ----------------------------------------------------------
# 小结：
# - 想让模型输出"程序能用的数据"，先用 Pydantic 把结构定义清楚
# - with_structured_output 比手写 JSON 解析稳，优先用它
# - 拿到的是对象，用 .字段 取值
#
# 踩坑：少数国产模型对 function calling 支持不稳；遇到报错可退回 JsonOutputParser，
#       或换支持更好的模型。学习阶段 DeepSeek 基本够用。
#
# 动手练习：定义一个 BugReport 模型（标题/严重级别/复现步骤），让模型从一段
#          描述里抽取出结构化的缺陷单——这正是测试岗能直接落地的场景。
# ----------------------------------------------------------
