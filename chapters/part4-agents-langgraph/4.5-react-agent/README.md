# 4.5 ReAct 工具循环：观察结果后再决定下一步

[全书目录](../../README.md) · [上一章 4.4](../4.4-state-reducer/README.md) · [下一章 4.6](../4.6-node-reliability/README.md)

- **目标**：搭出“想 → 做 → 把结果带回来再想”的 ReAct 工具循环，并了解它的现成封装。
- **前置**：4.3、1.5。
- **环境**：`react_loop.py` 离线；另外两个脚本调用真实模型（`DEEPSEEK_API_KEY`）。
- **命令**：`python tools/run_chapter.py 4.5 react_loop.py`

## 问题

1.5 里手写 while 循环调用工具很容易写错。LangGraph 把这个循环做成标准图：`agent` 节点调用模型，模型有 `tool_calls` 就去 `tools` 节点执行，结果回到 `agent`，没有就结束。

## 概念

- **ReAct**：Reasoning + Acting，想一步、调工具、看结果、再想，循环到能回答为止。
- **骨架**：`agent ⇄ tools` 两个节点加一条条件边（`tools_condition`）。用到 `MessagesState`（消息列表）、`ToolNode`（执行工具并生成 `ToolMessage`）。
- **现成封装**：这套骨架封装成 `create_react_agent`，一行得到等价的 Agent。LangChain v1 推荐的新入口是 `langchain.agents.create_agent`（底层仍是 LangGraph）；手搭学到的就是它内部那张图。
- **何时手搭**：需要自定义节点、分支或审批时手搭（4.12、4.14）；标准工具循环直接用现成的。

## 代码导读

按下面的顺序读，难度逐步增加：

| 文件 | 内容 | 需要模型 |
|---|---|---|
| [react_loop.py](react_loop.py) | 在 4.3 的合并图上改出 ReAct 结构，用纯函数模拟“是否还要调工具”，先看清循环结构 | 否 |
| [react_agent.py](react_agent.py) | 真实模型：先手搭 agent↔tools 循环，再用 `create_react_agent` 一行实现，并打印“想→做→再想”的完整轨迹 | 是 |
| [react_reliability.py](react_reliability.py) | 自定义 State 版：不用 `MessagesState`，把状态拆成字段，每个节点打印它改了什么；下一步仍由模型看 `tool_calls` 决定 | 是 |

## 练习

1. 运行 `react_loop.py`，指出它的节点分别对应 4.3 合并图里的哪个节点。
2. 在 `react_agent.py` 中问一个需要连续两步的问题（先乘再加），观察轨迹里的两次工具调用。
3. 在 `react_reliability.py` 里问“北京和上海，哪个更热？”，观察模型是否多次调用同一个工具。

## 运行与边界

- 真实模型的脚本会产生费用；模型可能选错工具，或不按预期停止，需要 `recursion_limit` 兜底。
- 本章的工具都是无副作用的示例；有副作用的工具需要授权与人工确认（4.11、4.12）。
- ReAct 与 Plan-and-Execute 的区别见 4.8。
