import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


# 1. 初始化模型
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 2. prompt：中间的 MessagesPlaceholder 是历史对话的插槽
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友善的助手，用简洁中文回答"),
    MessagesPlaceholder(variable_name="history"),  # 历史插这里
    ("human", "{question}"),                        # 本轮问题
])

# 3. 基础链：prompt → 模型 → 取纯文本
chain = prompt | llm | StrOutputParser()

# 4. 用字典当"记忆仓库"，按 session_id 分开存
store = {}

def get_session_history(session_id: str):
    if session_id not in store:                      # 第一次出现就建空历史
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 5. 给链套上"自动记忆"
chat = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",   # 用户输入 → prompt 的 {question}
    history_messages_key="history",  # 历史 → 那个 MessagesPlaceholder
)

# 6. 命令行循环
config = {"configurable": {"session_id": "user_001"}}  # 同一个 id = 同一段记忆
print("开始聊天（输入 quit 退出）")
while True:
    q = input("你：").strip()
    if q == "quit":
        break
    answer = chat.invoke({"question": q}, config=config)
    print("助手：", answer, "\n")