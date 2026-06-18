"""
Day 4 · 让对话记住上文（多轮记忆）
==========================================================
测试工程师转 AI 应用开发

大模型默认"没有记忆"：每次调用都是独立的，它不知道你上一句说了啥。
这一节给对话加上记忆，让它能多轮连续聊。

知识点：
1. 为什么模型默认无记忆（每次 invoke 互相独立）
2. MessagesPlaceholder：在 prompt 里留一个"历史对话"的插槽
3. RunnableWithMessageHistory：自动把历史塞进去、再把新对话存起来
4. session_id：区分不同用户/会话，避免记忆串台

产出：一个能记住你名字的三轮对话
==========================================================
"""

import os
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# RunnableWithMessageHistory 在新版会提示弃用警告；学习阶段先忽略，
# 生产里更推荐 LangGraph 的 checkpoint（本系列后面进阶时会讲）。
warnings.filterwarnings("ignore")
load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# prompt 里多了一个 MessagesPlaceholder：它就是"历史对话插这里"的占位槽。
# 每轮调用时，框架会自动把之前的对话填进这个槽，模型就能看到上下文。
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友善的助手，用简洁中文回答"),
    MessagesPlaceholder(variable_name="history"),   # ← 历史对话的插槽
    ("human", "{question}"),                          # ← 本轮新问题
])

# 基础链：和前几天一样，prompt → 模型 → 取纯文本
chain = prompt | llm | StrOutputParser()

# 用一个字典当"记忆仓库"，按 session_id 把不同会话的历史分开存。
store = {}

def get_session_history(session_id: str):
    """没见过的 session_id 就建一段空历史，见过的就取出来。"""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 给链套上"自动记忆"：
#   - input_messages_key   告诉它用户输入对应 prompt 里的哪个变量（question）
#   - history_messages_key 告诉它历史要填进哪个槽（history）
chat = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

# 同一个 session_id = 同一段记忆。换个 id 就是另一个互不相干的会话。
config = {"configurable": {"session_id": "user_001"}}

print("第1轮：", chat.invoke({"question": "我叫小明，在学 LangChain"}, config=config))
print("第2轮：", chat.invoke({"question": "我刚才说我在学什么？"}, config=config))
print("第3轮：", chat.invoke({"question": "我叫什么名字？"}, config=config))


# ----------------------------------------------------------
# 小结：
# - 模型本身无状态；记忆是"把历史对话每次重新喂给它"实现的
# - MessagesPlaceholder 是历史插槽，session_id 负责隔离不同会话
# - InMemoryChatMessageHistory 存在内存里，程序一关就没了；
#   要持久化得存文件/数据库，后面 LangGraph 的 checkpoint 是更好的方案
#
# 动手练习：把 session_id 换成两个不同的值各聊几句，验证两段记忆互不影响
# ----------------------------------------------------------
