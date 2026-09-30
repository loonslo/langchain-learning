# 第 4 篇：Agent 与 LangGraph

先判断是否需要模型决策，再学习状态、节点、分支、合并、恢复与协作。每个循环都要说明失败和终止。

先修：第 1 篇（4.9 会用到 3.6 的 LangSmith 追踪，建议先学）。

- [4.1 Agent 模式：先决定控制权放在哪里](4.1-agent-patterns/README.md)（离线）
- [4.2 LangGraph 基础：一份状态经过两个节点](4.2-langgraph-basics/README.md)（离线）
- [4.3 分支与循环：每条路线都要有出口](4.3-branch-loop/README.md)（离线 + 真实模型）
- [4.4 状态合并与 Reducer：并行结果如何留下来](4.4-state-reducer/README.md)（离线）
- [4.5 ReAct 工具循环：观察结果后再决定下一步](4.5-react-agent/README.md)（离线 + 真实模型）
- [4.6 节点可靠性：失败之后如何继续](4.6-node-reliability/README.md)（离线，一处需真实模型）
- [4.7 结构化路由：把模型选择限制在可验证集合](4.7-structured-routing/README.md)（真实模型）
- [4.8 规划与执行：让计划进度成为显式状态](4.8-plan-and-execute/README.md)（离线 + 真实模型）
- [4.9 可观测性：把运行过程留成证据](4.9-observability/README.md)（离线）
- [4.10 检查点与上下文：恢复流程和管理对话](4.10-checkpoint-context/README.md)（真实模型）
- [4.11 流式与人工介入：暂停在需要决定的位置](4.11-streaming-hitl/README.md)（离线，需终端输入）
- [4.12 搜索工具与信任边界：资料不能替你发号施令](4.12-tool-safety-search/README.md)（真实模型）
- [4.13 Text2SQL：先验证查询，再访问结构化数据](4.13-text2sql-agent/README.md)（离线）
- [4.14 Supervisor 与并行：多角色协作需要明确交接](4.14-supervisor-fanout/README.md)（真实模型）
- [4.15 框架取舍：先写需求，再选择工具](4.15-framework-landscape/README.md)（无代码）

[返回全书目录](../README.md)
