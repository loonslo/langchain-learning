# 4.3 分支与循环：每条路线都要有出口

[全书目录](../../README.md) · [上一章 4.2](../4.2-langgraph-basics/README.md) · [下一章 4.4](../4.4-state-reducer/README.md)

- **目标**：用条件边实现分支和循环，用 `recursion_limit` 防死循环，并对比手写循环，看清框架替你做了什么。
- **前置**：4.2、1.5、2.5。
- **环境**：`branch_loop_examples.py` 离线；`branch_loop.py` 前半段离线，后半段调用真实模型（`DEEPSEEK_API_KEY`）。
- **命令**：`python tools/run_chapter.py 4.3 branch_loop_examples.py`

## 问题

线性图和 LCEL 没区别。图真正的价值在分支、循环和状态：按当前状态决定走哪条边，把边指回前面的节点就形成循环，同时必须保证循环有出口。

## 概念

- **条件边**：`add_conditional_edges(源节点, 路由函数, 映射)`，路由函数读 state 并返回一个字符串，由映射决定去哪个节点或 `END`。
- **循环**：让条件边指回上游节点，并用计数器、达标条件等退出条件让它停下。
- **`recursion_limit`**：图执行的步数安全阀，超过就抛 `GraphRecursionError`。生产中的 Agent 必须配置。
- **框架替你做的事（harness）**：工具调用的解析（`tools_condition`）、执行与回灌（`ToolNode`）、循环控制、多轮记忆（checkpointer）、中断与恢复，手写循环里这些都要自己实现。

## 流程

`branch_loop_examples.py`（离线）：一个图同时体现三件事，用纯函数模拟：

1. 分支：`decide` 按待办列表决定去工具还是结束。
2. 循环：`run_tool` 执行完回到 `decide`，直到待办清空。
3. 使用工具：`run_tool` 节点执行处理步骤，结果写回 `history`。

`branch_loop.py`：

- 【一】质量分自循环：每轮质量加 1，达到 5 才结束；`recursion_limit=4` 时会被拦下并抛出 `GraphRecursionError`。离线。
- 【二】用 LangGraph 重写 1.5、2.5 的手写工具循环：`agent` 节点调模型，`ToolNode` 执行工具，`tools_condition` 判断是否继续，`InMemorySaver` 按 `thread_id` 提供多轮记忆。调用真实模型，并附一张“手写循环 vs LangGraph”对照表。

## 代码导读

先读 `branch_loop_examples.py`（不需要密钥），再读 `branch_loop.py`：先看【一】的 `route` 与 `build_loop`，再看【二】的 `build_agent` 与文件里的对照表。

## 练习

1. 把【一】里的达标线从 5 改成 8，`recursion_limit` 保持 4，观察被拦下时的输出。
2. 在【二】里用同一个 `thread_id` 追问“再加 100 呢”，确认模型能借助记忆理解“再加”；换一个 `thread_id` 再问，观察差别。
3. 对照表里的每一项，指出手写循环里对应的代码在哪里。

## 运行与边界

- `branch_loop.py` 的【二】会调用真实模型并产生费用。
- 路由目前用字符串返回，生产中更稳妥的做法是结构化输出路由，见 4.7。
