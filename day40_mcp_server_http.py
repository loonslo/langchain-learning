"""
Day 40（配套）· HTTP 远程 MCP 服务器
==========================================================
测试工程师转 AI 应用开发  ← 生产里 MCP 长什么样

stdio 服务器是"客户端把脚本当子进程拉起来"，只适合本地/同机练习。
生产里，工具服务通常是别的团队部署的一个常驻服务，你的 Agent 通过
网络连过去——这就是 HTTP 传输（streamable-http，MCP 现在推荐的远程传输）。

对比 day40_mcp_server.py：业务代码（工具怎么写）完全一样，
唯一区别是最后一行 mcp.run() 的 transport，以及要指定 host/port。
这正是 MCP 的价值：换传输不改业务。

运行（需要单独一个终端常驻）：
  pip install "mcp[cli]"
  python day40_mcp_server_http.py
启动后默认监听 http://127.0.0.1:8000/mcp ，再让 day40_mcp_agent.py 连它。
==========================================================
"""

from mcp.server.fastmcp import FastMCP

# host/port 在构造时指定；streamable-http 默认把服务挂在 /mcp 路径下
mcp = FastMCP("Weather", host="127.0.0.1", port=8000)


@mcp.tool()
def get_weather(city: str) -> str:
    """查询某城市的天气（演示用，返回写死的假数据）。"""
    fake = {
        "北京": "晴，26℃",
        "上海": "多云，29℃",
        "深圳": "雷阵雨，31℃",
    }
    return fake.get(city, f"暂无 {city} 的天气数据")


@mcp.tool()
def list_cities() -> list[str]:
    """列出所有支持查询的城市。"""
    return ["北京", "上海", "深圳"]


if __name__ == "__main__":
    # 和 stdio 版唯一的差别就在这一行：换成 streamable-http
    print("Weather MCP 服务器启动：http://127.0.0.1:8000/mcp（Ctrl+C 停止）")
    mcp.run(transport="streamable-http")


# ----------------------------------------------------------
# 小结：
# - 生产里 MCP 服务器多是常驻 HTTP 服务，Agent 走网络连接，而非本地子进程。
# - 从 stdio 切到 HTTP，业务代码零改动，只换 mcp.run 的 transport —— 这就是解耦。
# - 客户端侧对应地把连接配置从 command/args 换成 url，见 day40_mcp_agent.py。
# ----------------------------------------------------------
