import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是专业翻译，将用户输入翻译成{target_lang}，只输出译文，不加任何解释"),
    ("human", "{text}")
])

chain = prompt | llm | StrOutputParser()

# 交互式运行
while True:
    text = input("\n输入要翻译的内容（q退出）：")
    if text == "q":
        break
    lang = input("翻译成（英文/日文/法文）：")
    result = chain.invoke({"text": text, "target_lang": lang})
    print(f"译文：{result}")
