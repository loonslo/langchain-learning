import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 练习1：直接调用
response = llm.invoke("用一句话解释什么是 RAG")
print(response.content)

# 练习2：用 PromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个 Python 专家，用简洁的中文回答"),
    ("human", "{question}")
])

chain = prompt | llm | StrOutputParser()
result = chain.invoke({"question": "什么是装饰器？"})
print(result)
