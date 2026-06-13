import os

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气，输入城市名称"""
    data = {"北京": "晴天 25°C", "上海": "多云 22°C", "广州": "小雨 28°C"}
    return data.get(city, f"{city}暂无数据")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式，输入合法的Python数学表达式，如 '123 * 456'"""
    try:
        return str(eval(expression))
    except:
        return "计算失败，请检查表达式"

# 绑定工具给模型
llm_with_tools = llm.bind_tools([get_weather, calculate])

messages = [HumanMessage("北京天气怎么样？帮我算 99 * 88")]

# 第一轮：模型决定调用哪些工具
response = llm_with_tools.invoke(messages)
print(response.tool_calls)
messages.append(response)

# 执行工具，把结果追加进消息
tools_map = {"get_weather": get_weather, "calculate": calculate}
for tool_call in response.tool_calls:
    tool_result = tools_map[tool_call["name"]].invoke(tool_call["args"])
    messages.append(ToolMessage(
        content=str(tool_result),
        tool_call_id=tool_call["id"]
    ))

# 第二轮：模型根据工具结果给出最终回答
final_response = llm_with_tools.invoke(messages)
print("最终回答：", final_response.content)
print(final_response.tool_calls)