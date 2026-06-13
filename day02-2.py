import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个helpful助手"),
    MessagesPlaceholder(variable_name="history"),  # MessagePlaceholder占位符,历史消息插入这里
    ("human", "{question}")
])

chain = prompt | llm | StrOutputParser()

# 存储所有 session 的历史
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history"
)

# 模拟多轮对话
session = {"configurable": {"session_id": "user_001"}}

r1 = chain_with_memory.invoke({"question": "我叫小明，我在学LangChain"}, config=session)
print("第1轮：", r1)

r2 = chain_with_memory.invoke({"question": "我刚才说我在学什么？"}, config=session)
print("第2轮：", r2)

r3 = chain_with_memory.invoke({"question": "我叫什么名字？"}, config=session)
print("第3轮：", r3)