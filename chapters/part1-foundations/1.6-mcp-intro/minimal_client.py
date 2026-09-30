"""真实 MCP 子进程与协议调用，不使用 LLM 或 API Key。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def demo() -> int:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).with_name("minimal_server.py"))],
    )
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            listing = await session.list_tools()
            print("工具：", [tool.name for tool in listing.tools])
            result = await session.call_tool("add", {"a": 2, "b": 3})
            print(
                "结果：", [item.text for item in result.content if item.type == "text"]
            )
            if result.isError:
                return 1
            invalid = await session.call_tool("add", {"a": "不是整数", "b": 3})
            print("非法参数被拒绝：", bool(invalid.isError))
            return 0 if invalid.isError else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(demo()))
