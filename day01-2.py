import argparse
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. 创建解析器
parser = argparse.ArgumentParser(description="LangChain CLI 演示")
# 2. 添加参数
parser.add_argument("--mode", type=str, required=True,
                    choices=["translate", "explain"],
                    help="运行模式：translate(翻译) / explain(解释)")
parser.add_argument("--text", type=str, required=True,
                    help="要处理的文本")
parser.add_argument("--target-lang", type=str, default="中文",
                    help="翻译目标语言（默认：中文）")
# 3. 解析命令行
args = parser.parse_args()
# 初始化模型
llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
# 根据 mode 选择不同的 prompt
if args.mode == "translate":
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业翻译，只输出翻译结果，不做额外解释"),
        ("human", "将以下内容翻译成{target_lang}：\n{text}")
    ])
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"text": args.text, "target_lang": args.target_lang})
elif args.mode == "explain":
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是技术专家，用通俗的中文解释概念"),
        ("human", "解释以下概念：\n{text}")
    ])
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"text": args.text})

print(result)
