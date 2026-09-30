# 4.14 Supervisor 与并行：多角色协作需要明确交接

[全书目录](../../README.md) · [上一章 4.13](../4.13-text2sql-agent/README.md) · [下一章 4.15](../4.15-framework-landscape/README.md)

- **目标**：理解多 Agent 协作的三种形态：Supervisor 编排、Fan-out 并行、agent-as-tool 委派。
- **前置**：4.4、4.5、4.8；`DEEPSEEK_API_KEY`。
- **环境**：调用真实模型。
- **命令**：`python tools/run_chapter.py 4.14`

## 问题

单个 Agent 遇到“既要查资料、又要写、还要审”的复合任务会吃力。多 Agent 把任务拆给专家，由协调者串起来；但协调者怎么路由、并行分支怎么合并、子 Agent 的上下文怎么隔离，都要显式设计。

## 概念

- **Supervisor（编排）**：supervisor 节点按进度决定下一步交给哪个专家（research / writing / review），专家干完回到 supervisor，直到 `FINISH`。本质仍是“条件边 + 循环”，只是节点换成了 Agent。本章的 supervisor 不调用模型，按固定流水线确定性推进，并带步数护栏；让模型决定路由可能在 writing 与 review 之间反复，迟迟不结束，必须配硬约束。
- **Fan-out / Fan-in（并行）**：一个节点同时分叉到多个分支并行执行，再汇聚合并，适合“从不同角度各查一块、最后汇总”。并发分支写同一个字段，必须用 reducer（`Annotated[list, operator.add]`），否则报 `InvalidUpdateError`（4.4）。
- **agent-as-tool（委派）**：主流工具（如 Claude Code、Cursor、OpenAI Agents SDK）的做法：子 Agent 不是图上的节点，而是主 Agent 工具列表里的一个 tool。差别不是分工，而是省上下文：子 Agent 用独立的上下文，只收一段任务描述、只回一段结果摘要，主 Agent 看不到它的中间过程。

## 流程

`langgraph_supervisor.py` 三部分：

1. 【一】固定流水线的 Supervisor：research → writing → review → 结束，专家节点调用真实模型。
2. 【二】Fan-out：`topic` 分叉到多个角度并行，`angles` 用 `operator.add` 合并，最后 `merge_node` 汇总。
3. 【三】agent-as-tool：`run_delegating_agent` 把 `researcher`、`writer`、`reviewer` 作为工具交给主 Agent，最多 `max_steps` 步。

文件末尾有一张编排与委派的对比说明。

## 代码导读

[langgraph_supervisor.py](langgraph_supervisor.py)：先看 `PIPELINE`、`supervisor_node` 与 `route_by_supervisor`，再看 `FanState`，最后看 `_sub_agent` 与 `run_delegating_agent`。

## 练习

1. 运行三部分，比较图版本与委派版本的输出，说明谁看得到中间过程。
2. 去掉 `angles` 字段上的 `operator.add`，确认会抛出 `InvalidUpdateError`。
3. 学完 4.7 后，把 supervisor 改成让模型用结构化输出选择下一步，并保留 `max_steps` 护栏。

## 运行与边界

- 调用真实模型并产生费用，多 Agent 的调用次数比单 Agent 多得多。
- 多 Agent 增加了协调、延迟和调试成本；能用单 Agent 或工作流解决时，不要为了“多 Agent”而多 Agent。
