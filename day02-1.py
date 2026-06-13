import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# 初始化DeepSeek聊天模型
llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


class CodeReview(BaseModel):
    """代码审查结果的数据模型"""
    summary: str = Field(description="一句话总结这段代码做什么")
    issues: list[str] = Field(description="潜在问题列表，没有就空列表")
    score: int = Field(description="代码质量分，1-10分")


# 创建JSON输出解析器，用于将LLM输出转换为CodeReview对象
parser = JsonOutputParser(pydantic_object=CodeReview)

# 定义代码审查的提示模板
prompt = ChatPromptTemplate.from_template("""
你是代码审查专家，审查以下代码并给出评价。
{format_instructions}
代码：{code}
""")

# 构建完整的代码审查链：提示词 -> LLM -> JSON解析器
chain = prompt | llm | parser

# 执行代码审查示例
result = chain.invoke({
    "code": """
    def get_user(id):
        sql = f"SELECT * FROM users WHERE id = {id}"
        return db.execute(sql)
    """,
    "format_instructions": parser.get_format_instructions()
})

print(result)
print("评分：", result["score"])
print("问题：", result["issues"])


class SentimentResult(BaseModel):
    """情感分析结果的数据模型"""
    sentiment: str = Field(description="positive / negative / neutral")
    confidence: float = Field(description="置信度 0-1")
    keywords: list[str] = Field(description="触发情感的关键词")


# 创建情感分析的JSON输出解析器
parser2 = JsonOutputParser(pydantic_object=SentimentResult)

# 定义情感分析的提示模板
prompt2 = ChatPromptTemplate.from_template("""
分析以下文本的情感倾向。
{format_instructions}
文本：{text}
""")

# 构建情感分析链：提示词 -> LLM -> JSON解析器
chain2 = prompt2 | llm | parser2

# 准备待分析的文本样本
texts = [
    "今天跑通了第一行LangChain代码，感觉还不错",
    "学了三天还是看不懂，太难了，想放弃",
    "就那样吧，也没什么特别的感受"
]

# 批量处理文本并进行情感分析
for text in texts:
    result = chain2.invoke({
        "text": text,
        "format_instructions": parser2.get_format_instructions()
    })
    print(f"文本：{text}")
    print(f"情感：{result['sentiment']}，置信度：{result['confidence']}")
    print(f"关键词：{result['keywords']}\n")
