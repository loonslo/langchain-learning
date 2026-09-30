"""最小 MCP stdio 服务：只暴露一个无外部副作用的加法工具。"""

from mcp.server.fastmcp import FastMCP

server = FastMCP("chapter-1.6-math")


@server.tool()
def add(a: int, b: int) -> int:
    """两个整数相加；不访问网络、不写文件。"""
    return a + b


if __name__ == "__main__":
    server.run(transport="stdio")
