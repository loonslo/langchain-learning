"""
Day 40 · MCP：用标准协议给 Agent 接工具（客户端全景）
==========================================================
测试工程师转 AI 应用开发  ← 阶段3 工具集成事实标准

Day05/Day30 的工具是写死在代码里的 @tool。真实团队里，工具/数据源常由别的团队、
别的语言提供。MCP 让它们按统一协议暴露，Agent 端用一个客户端就能把这些
工具拉进来，和本地 @tool 一样用——这就是 2026 Agent 工具集成的事实标准。

本文件把客户端侧的常见用法一次讲全，按 demo 分段，可单独看：
  demo1 连服务器、拿工具、喂给 Agent（最核心）
  demo2 只拿单个服务器的工具 / 给工具传环境变量鉴权
  demo3 读 Resources（只读数据当上下文）
  demo4 取 Prompts（复用团队沉淀的问法）
  demo5 流式输出，边跑边看 Agent 每一步
  demo6 同时挂多个服务器（stdio + 远程 HTTP）

依赖：pip install langchain-mcp-adapters mcp
注意：MCP 客户端调用都是异步的，所以整体用 asyncio.run 跑。
==========================================================
"""

import asyncio
import os

# 本机 MCP 服务走直连，别被系统代理（Clash/VPN/公司代理）劫持到代理上。
# 否则连 127.0.0.1 也会被转发出去，代理回 502 Bad Gateway，导致 demo6 连不上。
# 必须在创建 httpx 客户端之前设置（httpx trust_env 会在连接时读这个变量）。
os.environ["NO_PROXY"] = "127.0.0.1,localhost,::1"

from common import get_llm

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent


def build_client() -> MultiServerMCPClient:
    """声明要连哪些 MCP 服务器。key 是你给服务器起的别名，value 是连接配置。"""
    return MultiServerMCPClient({
        # 本地服务器：把 day40_mcp_server.py 作为 stdio 子进程拉起来
        "math": {
            "command": "python",
            "args": ["day40_mcp_server.py"],
            "transport": "stdio",
            # env：给子进程传环境变量（API key、DB 连接串等），服务器用它鉴权。
            # 这里传对的密钥，服务器的 secure_ping 才放行。详见 demo2。
            "env": {"DEMO_TOKEN": "secret-123"},
        },
        # 远程服务器：连一个常驻 HTTP 服务（需先跑 day40_mcp_server_http.py）
        # 不用 command/args，改用 url；HTTP 系还可加 headers 做鉴权。
        "weather": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable_http",
            "headers": {"Authorization": "Bearer xxx"},  # 可选
        },
    })


# ==========================================================
# demo1：最核心用法——拿工具，交给 Agent，模型自己决定怎么调
# ==========================================================
async def demo1_tools_via_agent(client: MultiServerMCPClient):
    tools = await client.get_tools(server_name="math")   # 只取 math 服务器的工具
    print("demo1 · 拿到的工具：", [t.name for t in tools])

    agent = create_agent(get_llm(temperature=0), tools)
    result = await agent.ainvoke(
        {"messages": [("user", "用工具算 (12 + 8) 再乘以 3")]}
    )
    print("demo1 · 答：", result["messages"][-1].content)


# ==========================================================
# demo2：只取单个服务器的工具 + 通过 env/headers 给服务器传鉴权密钥
# ----------------------------------------------------------
# get_tools(server_name=...) 只拉某一个服务器的工具（demo1 已用到）。
# 重点看鉴权：stdio 用 "env" 注入密钥，HTTP 用 "headers"（如 Authorization），
# 服务器读到后决定放不放行——业务代码不变，换传输只换密钥放哪。
# ==========================================================
async def demo2_single_server_and_auth():
    # 1) 正确密钥：env 里注入 DEMO_TOKEN=secret-123，受保护工具放行
    ok_client = MultiServerMCPClient({
        "math": {
            "command": "python",
            "args": ["day40_mcp_server.py"],
            "transport": "stdio",
            "env": {"DEMO_TOKEN": "secret-123"},      # ← 正确密钥
        },
    })
    tools = await ok_client.get_tools(server_name="math")   # 只取 math 一个服务器
    print("demo2 · math 的工具：", [t.name for t in tools])

    secure = next(t for t in tools if t.name == "secure_ping")
    print("demo2 · 正确密钥：", await secure.ainvoke({}))

    # 2) 错误密钥：同一个工具会被服务器拒绝（鉴权失败信息回传回来）
    bad_client = MultiServerMCPClient({
        "math": {
            "command": "python",
            "args": ["day40_mcp_server.py"],
            "transport": "stdio",
            "env": {"DEMO_TOKEN": "wrong"},           # ← 错误密钥
        },
    })
    bad_tools = await bad_client.get_tools(server_name="math")
    bad_secure = next(t for t in bad_tools if t.name == "secure_ping")
    try:
        print("demo2 · 错误密钥：", await bad_secure.ainvoke({}))
    except Exception as e:  # noqa: BLE001
        print("demo2 · 错误密钥被拒绝：", e)


# ==========================================================
# demo3：读 Resources —— 把只读数据当作 Agent 的背景上下文
# ----------------------------------------------------------
# Resource 不是"动作"，是"数据"。这里直接按 URI 读出来，
# 拿到的是 LangChain Blob，可以塞进 prompt 当上下文，或做 RAG 的一份来源。
# ==========================================================
async def demo3_resources(client: MultiServerMCPClient):
    blobs = await client.get_resources("math", uris="config://app-version")
    print("demo3 · 读到的资源内容：", [b.as_string() for b in blobs])

    # 模板资源（URI 带参数）要显式给出具体 URI 才能读
    doc = await client.get_resources("math", uris="docs://add")
    print("demo3 · add 的文档：", [b.as_string() for b in doc])


# ==========================================================
# demo4：取 Prompts —— 复用服务器沉淀的"问法"，再交给 Agent
# ----------------------------------------------------------
# get_prompt 返回的就是一组对话消息，可以直接当 Agent 的输入。
# 好处：问法收敛在服务器端，客户端不用各写各的 prompt。
# ==========================================================
async def demo4_prompts(client: MultiServerMCPClient):
    messages = await client.get_prompt(
        "math", "word_problem",
        arguments={"text": "买 3 箱苹果，每箱 8 个，一共多少个？"},
    )
    print("demo4 · 模板生成的消息：", messages[0].content)

    tools = await client.get_tools(server_name="math")
    agent = create_agent(get_llm(temperature=0), tools)
    result = await agent.ainvoke({"messages": messages})  # 直接喂模板消息
    print("demo4 · 答：", result["messages"][-1].content)


# ==========================================================
# demo5：流式输出 —— 边跑边看 Agent 的每一步（调了哪个工具、返回什么）
# ----------------------------------------------------------
# .astream 逐步吐出中间状态，适合做进度展示 / 调试 Agent 轨迹。
# ==========================================================
async def demo5_streaming(client: MultiServerMCPClient):
    tools = await client.get_tools(server_name="math")
    agent = create_agent(get_llm(temperature=0), tools)

    print("demo5 · 流式过程：")
    async for chunk in agent.astream(
        {"messages": [("user", "用工具算 25 乘以 4，再加 10")]},
        stream_mode="values",
    ):
        last = chunk["messages"][-1]
        last.pretty_print()   # 打印每一步的最新消息（工具调用 / 工具结果 / 回答）


# ==========================================================
# demo6：多服务器混合 —— 本地 math + 远程 weather，一次问跨两个服务器
# ----------------------------------------------------------
# 不带 server_name 的 get_tools() 会汇总所有服务器的工具，模型自动路由。
# 远程服务器没起时会连不上，这里 try 一下给出友好提示。
# ==========================================================
async def demo6_multi_server(client: MultiServerMCPClient):
    try:
        tools = await client.get_tools()   # 汇总所有服务器的工具
    except Exception as e:
        print(f"demo6 · 连不上远程 weather（先跑 python day40_mcp_server_http.py）：{e}")
        return

    print("demo6 · 全部工具：", [t.name for t in tools])
    agent = create_agent(get_llm(temperature=0), tools)
    result = await agent.ainvoke(
        {"messages": [("user", "北京天气怎么样？顺便算一下 6 乘以 7")]}
    )
    print("demo6 · 答：", result["messages"][-1].content)


async def main():
    client = build_client()
    await demo1_tools_via_agent(client)
    await demo2_single_server_and_auth()
    await demo3_resources(client)
    await demo4_prompts(client)
    await demo5_streaming(client)
    await demo6_multi_server(client)   # 需要先启动 HTTP 服务器，否则会跳过


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ModuleNotFoundError as e:
        print(f"(缺依赖：pip install langchain-mcp-adapters mcp) {e}")


# ----------------------------------------------------------
# 小结：
# - 连接配置：key=服务器别名，transport 决定"怎么连"；stdio 用 command/args（+env），
#   HTTP 用 url（+headers 鉴权）。换服务器/换传输，Agent 业务代码不动。
# - 客户端能从服务器拿三种东西：get_tools（动作）、get_resources（只读数据）、
#   get_prompt（复用问法）。工具喂给 create_agent，模型自己决定何时调。
# - get_tools() 不带名字=汇总所有服务器，模型自动跨服务器路由；带 server_name=只取一个。
# - .ainvoke 一次拿结果；.astream 逐步看轨迹，适合展示进度和调试。
#
# 了解：A2A（Agent-to-Agent）是另一层协议——MCP 解决"Agent↔工具"，
#       A2A 解决"Agent↔Agent"之间怎么通信协作。前沿，能聊即可。
#
# 动手练习：给 day40_mcp_server_http.py 再加一个"查空气质量"工具，
#           启动它，然后问一句同时用到天气、空气、数学三个工具的混合任务。
# ----------------------------------------------------------
