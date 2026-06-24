"""
Day 40 · MCP：用标准协议给 Agent 接工具
==========================================================
测试工程师转 AI 应用开发  ← 阶段3 工具集成事实标准

Day25/26 的工具是写死在代码里的 @tool。真实团队里，工具/数据源常由别的团队、
别的语言提供。MCP 让它们按统一协议暴露，Agent 端用一个客户端就能把这些
工具拉进来，和本地 @tool 一样用——这就是 2026 Agent 工具集成的事实标准。

本节：用 MultiServerMCPClient 连上 day31_mcp_server.py，把它的工具
交给 create_react_agent，让模型像调本地工具一样调 MCP 工具。

依赖：pip install langchain-mcp-adapters mcp
注意：get_tools() 是异步的，所以用 asyncio.run 跑。
==========================================================
"""

import asyncio
from common import get_llm


async def main():
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.prebuilt import create_react_agent

    # 声明要连哪些 MCP 服务器。这里把本地 day31_mcp_server.py 作为 stdio 子进程拉起
    client = MultiServerMCPClient({
        "math": {
            "command": "python",
            "args": ["day31_mcp_server.py"],
            "transport": "stdio",
        },
        # 还可以再挂别的服务器，比如文件系统、数据库、第三方 MCP（即插即用）
    })

    tools = await client.get_tools()      # 把 MCP 工具转成 LangChain 工具
    print("从 MCP 拿到的工具：", [t.name for t in tools])

    agent = create_react_agent(get_llm(temperature=0), tools)
    result = await agent.ainvoke(
        {"messages": [("user", "用工具算 (12 + 8) 再乘以 3")]}
    )
    print("答：", result["messages"][-1].content)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ModuleNotFoundError as e:
        print(f"(缺依赖：pip install langchain-mcp-adapters mcp) {e}")


# ----------------------------------------------------------
# 小结：
# - MCP = 工具/数据源的"统一插座"：工具方按协议暴露，Agent 端一个客户端即插即用。
# - MultiServerMCPClient 可同时挂多个服务器；get_tools() 把它们转成 LangChain 工具，
#   之后和本地 @tool 完全一样喂给 create_react_agent。
# - 价值：换工具/加数据源不改 Agent 代码，跨团队、跨语言复用——所以是事实标准。
#
# 了解：A2A（Agent-to-Agent）是另一层协议——MCP 解决"Agent↔工具"，
#       A2A 解决"Agent↔Agent"之间怎么通信协作。前沿，能聊即可。
#
# 动手练习：再写一个 MCP 服务器暴露"查天气"，在 client 里多挂一个，问混合任务。
# ----------------------------------------------------------
