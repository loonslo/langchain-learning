"""
Day 40（配套）· 一个最小 MCP 服务器：Tools + Resources + Prompts
==========================================================
测试工程师转 AI 应用开发  ← 阶段3 工具集成事实标准

这是给 day40_mcp_agent.py 连接用的 MCP 服务器，单独一个进程。
MCP（Model Context Protocol）是"给 Agent 接工具/数据源的统一插座"：
工具方按 MCP 标准把能力暴露出来，任何支持 MCP 的客户端都能即插即用，
不用为每个框架各写一套适配。这就是它要解决的问题——工具集成的事实标准。

MCP 服务器能暴露的不止"工具"，一共三种原语（面试常问）：
  1. Tools     —— 可被模型调用、会产生副作用的"动作"（查库、算数、发消息）
  2. Resources —— 只读的"数据/上下文"，像文件或 GET 接口（配置、文档、数据快照）
  3. Prompts   —— 预设的提示词模板，把团队沉淀的"问法"复用给任何客户端

这里用官方 mcp SDK 的 FastMCP 把三种都演示一遍，走 stdio 传输。
依赖：pip install mcp
（一般不用手动运行它，day40_mcp_agent.py 会把它作为子进程拉起来。）
==========================================================
"""

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

# 客户端连接配置里的 "env"（stdio）/ "headers"（HTTP）会把密钥传进来。
# stdio 场景：这些 env 注入到本子进程的环境变量，服务器启动时读它做鉴权——
# 这就是 MCP 给工具服务传 API key / DB 密码最常见的方式。见 agent 的 demo2。
_API_KEY = os.environ.get("DEMO_TOKEN", "")


# ==========================================================
# 一、Tools：模型可以"调用"的动作
# ----------------------------------------------------------
# 关键点：类型注解 + docstring 不是可选项——FastMCP 用它们自动生成
# JSON Schema，模型正是靠这份 schema 决定"传什么参数、什么时候调"。
# 所以工具的 docstring 要写清"做什么、参数含义"，这就是给模型看的说明书。
# ==========================================================

@mcp.tool()
def add(a: int, b: int) -> int:
    """两个整数相加。"""
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """两个整数相乘。"""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """两个数相除，返回 a / b。b 为 0 时报错。"""
    # 工具内部要显式处理错误：抛出的异常会被 MCP 打包成"工具执行失败"
    # 回传给模型，模型能读到原因并改口重试或换方案——健壮工具的基本功。
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b


@mcp.tool()
async def fetch_rate(base: str, quote: str) -> float:
    """查询汇率（演示用，返回写死的假数据）。工具也可以是 async 的。"""
    # 真实场景这里会 await 一个 HTTP 请求 / 数据库查询。
    # FastMCP 原生支持异步工具，I/O 密集的活儿用 async 不阻塞其它请求。
    fake_rates = {("USD", "CNY"): 7.18, ("CNY", "USD"): 0.139}
    return fake_rates.get((base.upper(), quote.upper()), 1.0)


@mcp.tool()
def secure_ping() -> str:
    """受保护的工具：只有客户端传入正确的 DEMO_TOKEN 才放行（演示 env 鉴权）。"""
    # _API_KEY 来自客户端注入的环境变量；密钥不对就抛错，MCP 会把失败回传给客户端。
    # 真实场景这里换成校验 JWT / 查权限 / 比对 API key。
    if _API_KEY != "secret-123":
        raise ValueError("未授权：DEMO_TOKEN 无效或缺失")
    return "pong（已通过 env 鉴权）"


# ==========================================================
# 二、Resources：只读的数据/上下文（不产生副作用）
# ----------------------------------------------------------
# 每个 Resource 有一个 URI（像文件路径）。客户端按 URI 读取内容。
# 用途：把"配置、文档、数据快照"喂给 Agent 当背景知识，而不是当动作。
# ==========================================================

@mcp.resource("config://app-version")
def app_version() -> str:
    """静态资源：固定 URI，直接返回内容。"""
    return "MathServer v1.2.0"


@mcp.resource("docs://{topic}")
def get_doc(topic: str) -> str:
    """模板资源：URI 里带参数 {topic}，按主题动态返回文档片段。"""
    docs = {
        "add": "add(a, b)：整数相加，用于累加、计数场景。",
        "multiply": "multiply(a, b)：整数相乘，用于面积、批量计价场景。",
    }
    return docs.get(topic, f"暂无关于 '{topic}' 的文档。")


# ==========================================================
# 三、Prompts：可复用的提示词模板
# ----------------------------------------------------------
# 把团队里"好用的问法"沉淀成模板，任何客户端都能拉取后直接用。
# 返回值会被转成对话消息，客户端拿到后可以直接喂给模型。
# ==========================================================

@mcp.prompt()
def word_problem(text: str) -> str:
    """把一段应用题包装成"必须用工具逐步计算"的提示词。"""
    return (
        f"这是一道应用题：{text}\n"
        "要求：不要口算，必须调用可用的数学工具逐步计算，"
        "最后用一句话给出结果。"
    )


if __name__ == "__main__":
    # stdio：客户端通过标准输入输出和本进程通信（最简单的本地传输方式）
    mcp.run(transport="stdio")


# ----------------------------------------------------------
# 小结：
# - 一个 MCP 服务器可同时暴露 Tools / Resources / Prompts 三种原语：
#     Tools=动作、Resources=只读数据、Prompts=复用的问法。
# - 工具的类型注解 + docstring 就是给模型看的"说明书"，直接决定调用效果。
# - 工具内部要显式抛错，失败信息会回传给模型；I/O 活儿可用 async 工具。
# - 换传输只改最后一行 mcp.run(...)，业务代码一行不动 → 见 day40_mcp_server_http.py。
# ----------------------------------------------------------
