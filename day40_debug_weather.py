"""
Day40 诊断：单独连远程 weather MCP 服务器，把被库盖住的真实错误挖出来
==========================================================
背景：day40_mcp_agent.py 的 demo6 报 UnboundLocalError('tools')，
这是 langchain-mcp-adapters 0.3.0 的已知 bug——连接失败时它自己又抛了个
二次错误，把"为什么连不上"的原始异常盖住了。

这个脚本绕过 create_agent，直接用 mcp 客户端连 weather，
并且递归展开 ExceptionGroup，打印每一个子异常的完整堆栈。
先确认 day40_mcp_server_http.py 已经在另一个终端跑着，再运行本文件。

运行：python day40_debug_weather.py
==========================================================
"""

import asyncio
import traceback

URL = "http://127.0.0.1:8000/mcp"          # 注意：稍后可试试结尾加斜杠 /mcp/
HEADERS = {"Authorization": "Bearer xxx"}   # 和 agent 里保持一致；可试着删掉它


def show(exc: BaseException, depth: int = 0):
    """递归打印异常（含 ExceptionGroup 的每个子异常）。"""
    pad = "  " * depth
    print(f"{pad}└─ {type(exc).__name__}: {exc}")
    subs = getattr(exc, "exceptions", None)  # ExceptionGroup 才有
    if subs:
        for sub in subs:
            show(sub, depth + 1)
    else:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        print("\n".join(pad + "   " + ln for ln in tb.rstrip().splitlines()))


async def probe(url: str, headers: dict | None):
    """直连 MCP 服务器，list 出工具。成功返回工具名，失败原样抛出。"""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return [t.name for t in resp.tools]


async def main():
    # 依次尝试：原样 / 去掉鉴权头 / 结尾加斜杠——哪个成了就知道根因在哪
    trials = [
        ("原样（带 Authorization 头）", URL, HEADERS),
        ("去掉 Authorization 头", URL, None),
        ("URL 结尾加斜杠 /mcp/", URL.rstrip("/") + "/", HEADERS),
    ]
    for label, url, headers in trials:
        print(f"\n=== 尝试：{label} -> {url} ===")
        try:
            names = await probe(url, headers)
            print(f"✅ 连上了！工具：{names}")
            print("   → 用这个配置回填到 day40_mcp_agent.py 的 weather 里即可。")
            return
        except Exception as e:  # noqa: BLE001
            print("❌ 失败，真实异常如下：")
            show(e)
    print("\n三种都失败了。把上面的堆栈发我，就能定位根因。")


if __name__ == "__main__":
    asyncio.run(main())
