"""
Day 6 · 综合小项目：命令行聊天机器人
==========================================================
测试工程师转 AI 应用开发

这是第一个"把前面学的东西合起来"的项目，用到：
  - Day1 LCEL 链      - Day4 多轮记忆      - Day5 工具调用
功能：多角色（Python老师/计算器/自由聊天）+ 记忆 + 内置计算器工具 + 保存对话

这一节的重点不是新知识，而是体会"零件怎么拼成一个能用的东西"。
==========================================================
"""

import os
import warnings
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool

warnings.filterwarnings("ignore")
load_dotenv()


# ---------- 工具：带安全限制的计算器 ----------
@tool
def calculator(expression: str) -> str:
    """计算数学表达式。规则：
    - 乘方用 **（例如 2**10），不要用 ^
    - 开方用 sqrt(x)（例如 sqrt(16)）
    - 支持 sin / cos / log 等 math 模块函数
    """
    import math
    try:
        # 第二、三个参数限制可用的名字：禁用内置函数，只放开 math，避免 eval 被滥用
        return str(eval(expression, {"__builtins__": {}}, vars(math)))
    except Exception as e:
        return f"计算失败：{e}"


llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
llm_with_tools = llm.bind_tools([calculator])


# ---------- 角色预设 ----------
ROLES = {
    "1": ("Python老师", "你是一个耐心的 Python 编程老师，用简洁中文解答，适当举例"),
    "2": ("计算器", "你是一个计算助手，需要算数时调用 calculator 工具"),
    "3": ("自由聊天", "你是一个友善的聊天伙伴，随意聊天"),
}


def choose_role():
    print("\n选择角色：")
    for k, (name, _) in ROLES.items():
        print(f"  {k}. {name}")
    choice = input("请选择（默认 2）：").strip() or "2"
    return ROLES.get(choice, ROLES["2"])


def save_history(role_name, messages):
    """退出时把对话存成 txt，方便复盘。"""
    filename = f"chat_{role_name}_{datetime.now():%Y%m%d_%H%M}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for msg in messages:
            who = "你" if msg.__class__.__name__ == "HumanMessage" else role_name
            f.write(f"{who}：{msg.content}\n\n")
    print(f"\n对话已保存到 {filename}")


def main():
    role_name, system_prompt = choose_role()
    print(f"\n已选择：{role_name}（输入 clear 清除记忆，quit 退出）\n")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])

    history = InMemoryChatMessageHistory()   # 这个项目只有一个会话，直接用一份历史

    while True:
        user_input = input("你：").strip()
        if not user_input:
            continue
        if user_input == "quit":
            save_history(role_name, history.messages)
            break
        if user_input == "clear":
            history.clear()
            print("记忆已清除\n")
            continue

        # 用模板把"系统设定 + 历史 + 本轮问题"组织成消息列表
        messages = prompt.format_messages(history=history.messages, question=user_input)
        response = llm_with_tools.invoke(messages)

        if response.tool_calls:
            # 模型决定调工具：执行 → 把结果喂回 → 再让模型给最终答（Day5 的两轮流程）
            messages.append(response)
            for call in response.tool_calls:
                result = calculator.invoke(call["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
            final = llm_with_tools.invoke(messages)
            answer = final.content
        else:
            answer = response.content

        print(f"{role_name}：{answer}\n")
        # 手动把这一轮存进历史（只存用户和最终回答，工具中间步骤不入历史）
        history.add_user_message(user_input)
        history.add_ai_message(answer)


if __name__ == "__main__":
    main()


# ----------------------------------------------------------
# 小结：
# - 一个真实小应用 = 记忆 + 工具 + 角色设定 + 输入输出循环 拼起来
# - 工具的中间步骤不必塞进长期历史，只留"用户问 + 最终答"更干净
#
# 动手练习：给它再加一个工具（比如查询当前时间），看模型会不会在该用的时候自己调
# ----------------------------------------------------------
