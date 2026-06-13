import os
import warnings

warnings.filterwarnings("ignore")

from datetime import datetime
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

# 角色预设
ROLES = {
    "1": ("Python老师", "你是一个耐心的Python编程老师，用简洁中文解答编程问题，适当举例"),
    "2": ("英语老师", "你是一个英语老师，帮助用户学习英语，纠正语法错误，解释表达方式"),
    "3": ("自由聊天", "你是一个友善的聊天伙伴，随意聊天")
}


def choose_role():
    print("\n选择角色：")
    for k, (name, _) in ROLES.items():
        print(f"  {k}. {name}")
    choice = input("请选择（默认3）：").strip() or "3"
    return ROLES.get(choice, ROLES["3"])


def save_history(role_name, messages):
    filename = f"chat_{role_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for msg in messages:
            role = "你" if msg.__class__.__name__ == "HumanMessage" else role_name
            f.write(f"{role}：{msg.content}\n\n")
    print(f"\n对话已保存到 {filename}")


def main():
    role_name, system_prompt = choose_role()
    print(f"\n已选择：{role_name}，开始对话（clear清除记忆，quit退出）\n")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])

    chain = prompt | llm | StrOutputParser()

    store = {}

    def get_history(session_id):
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]

    chain_with_memory = RunnableWithMessageHistory(
        chain, get_history,
        input_messages_key="question",
        history_messages_key="history"
    )

    session_id = "main"
    config = {"configurable": {"session_id": session_id}}

    while True:
        user_input = input("你：").strip()
        if not user_input:
            continue
        if user_input == "quit":
            save_history(role_name, store.get(session_id,
                                              InMemoryChatMessageHistory()).messages)
            break
        if user_input == "clear":
            store[session_id] = InMemoryChatMessageHistory()
            print("记忆已清除\n")
            continue

        response = chain_with_memory.invoke(
            {"question": user_input}, config=config
        )
        print(f"{role_name}：{response}\n")


if __name__ == "__main__":
    main()
