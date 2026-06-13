import os
import warnings

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
warnings.filterwarnings("ignore")

from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory


@tool
def calculator(expression: str) -> str:
    """使用calculator计算问题
       规则：
    - 乘方用 ** ，例如 2**10
    - 不能用 ^
    - 开方用 sqrt(x)，例如 sqrt(16)
    - 支持 sin/cos/log 等math模块函数
    """
    import math
    try:
        return str(eval(expression, {"__builtins__": {}}, vars(math)))
    except Exception as e:
        return f"计算失败：{e}"


llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
llm_with_tools = llm.bind_tools([calculator])

# 角色预设
ROLES = {
    "1": ("Python老师", "你是一个耐心的Python编程老师，用简洁中文解答编程问题，适当举例"),
    "2": ("计算器", "你是一个计算器"),
    "3": ("自由聊天", "你是一个友善的聊天伙伴，随意聊天")
}


def choose_role():
    print("\n选择角色：")
    for k, (name, _) in ROLES.items():
        print(f"  {k}. {name}")
    choice = input("请选择（默认2）：").strip() or "2"
    return ROLES.get(choice, ROLES["2"])


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

    store = {}

    def get_history(session_id):
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]

    session_id = "main"

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

        history = get_history(session_id)
        # 用 prompt 模板来组织消息，而不是手拼
        messages = prompt.format_messages(
            history=history.messages,
            question=user_input
        )

        response = llm_with_tools.invoke(messages)

        if response.tool_calls:
            tool_result = calculator.invoke(response.tool_calls[0]["args"])
            messages.append(response)
            messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=response.tool_calls[0]["id"]
            ))
            final = llm_with_tools.invoke(messages)
            print(f"{role_name}：{final.content}\n")
            history.add_user_message(user_input)
            history.add_ai_message(final.content)
        else:
            print(f"{role_name}：{response.content}\n")
            history.add_user_message(user_input)
            history.add_ai_message(response.content)


if __name__ == "__main__":
    main()
