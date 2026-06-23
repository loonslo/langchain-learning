"""
Day 5 · 让模型会用工具（Tool Calling）
==========================================================
测试工程师转 AI 应用开发

模型只会"说"，不会"做"——它算不准大数、查不到实时天气。
工具调用让模型能在需要时"调用你写的函数"，拿到真实结果再回答。
这是后面 Agent（智能体）的地基。

知识点：
1. @tool 装饰器：把普通函数变成模型能调用的工具，docstring 至关重要
2. llm.bind_tools()：把工具清单绑给模型
3. 工具调用的"两轮流程"：模型先决定调哪个工具 → 你执行 → 把结果喂回 → 模型给最终答
4. 怎么判断模型到底想不想调工具（看 tool_calls，不是看 content）

产出：一个能自己决定"算数学题用计算器、查天气用天气工具"的对话
==========================================================
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


# @tool 把函数注册成"工具"。
# 注意：docstring 不是写给人看的，是写给模型看的——模型靠它判断"这个工具干嘛、啥时候用"。
# docstring 写得越清楚，模型选工具越准。这是 tool 最关键的部分。
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气，输入城市名称，例如 '北京'"""
    data = {"北京": "晴天 25°C", "上海": "多云 22°C", "广州": "小雨 28°C"}
    return data.get(city, f"{city}暂无数据")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式，输入合法的 Python 数学表达式，例如 '99 * 88'"""
    try:
        return str(eval(expression))
    except Exception:
        return "计算失败，请检查表达式"


# 把工具清单绑给模型。绑完后模型在回答时，可以选择"我要调用某个工具"。
llm_with_tools = llm.bind_tools([get_weather, calculate])
print(llm_with_tools)
# ---------- 工具调用的完整两轮流程 ----------
messages = [HumanMessage("北京天气怎么样？再帮我算 99 * 88")]
print(messages)
# 第一轮：模型不直接回答，而是返回"我要调用哪些工具、参数是什么"（tool_calls）
response = llm_with_tools.invoke(messages)
print("模型决定调用的工具：", response)
messages.append(response)   # 把模型这步决定也加进对话历史
print(messages)
# 你来真正执行这些工具，把结果用 ToolMessage 追加回去
tools_map = {"get_weather": get_weather, "calculate": calculate}
for call in response.tool_calls:
    print('call')
    print(call)
    result = tools_map[call["name"]].invoke(call["args"])
    messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
    print('message')
    print(messages)

# 第二轮：模型看到工具返回的真实结果，给出给用户的最终回答
final = llm_with_tools.invoke(messages)
print(final)
print("最终回答：", final.content)


# ----------------------------------------------------------
# 小结：
# - @tool 的 docstring 是模型选工具的依据，务必写清楚"干嘛、参数是什么"
# - 流程是两轮：模型给 tool_calls → 你执行 → 喂回结果 → 模型给最终答
# - 判断模型是否要调工具：看 response.tool_calls 是否为空，
#   不要看 response.content（有的模型调工具时 content 也会有内容）
#
# 安全提醒（重要）：真实项目里绝不要把"删除/转账/发邮件"这类危险操作
#   直接做成工具让模型自由调用，必须加人工确认。后面 Agent 阶段会专门讲。
# ----------------------------------------------------------
