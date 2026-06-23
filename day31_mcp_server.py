"""
Day 31（配套）· 一个最小 MCP 服务器
==========================================================
测试工程师转 AI 应用开发

这是给 day31_mcp_agent.py 连接用的 MCP 服务器，单独一个进程。
MCP（Model Context Protocol）是"给 Agent 接工具/数据源的统一插座"：
工具方按 MCP 标准把能力暴露出来，任何支持 MCP 的客户端都能即插即用，
不用为每个框架各写一套适配。这就是它要解决的问题——工具集成的事实标准。

这里用官方 mcp SDK 的 FastMCP 暴露两个工具，走 stdio 传输。
依赖：pip install mcp
（一般不用手动运行它，day31_mcp_agent.py 会把它作为子进程拉起来。）
==========================================================
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")


@mcp.tool()
def add(a: int, b: int) -> int:
    """两个整数相加。"""
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """两个整数相乘。"""
    return a * b


if __name__ == "__main__":
    # stdio：客户端通过标准输入输出和本进程通信（最简单的本地传输方式）
    mcp.run(transport="stdio")
