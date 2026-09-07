# 原 Day31～40 文件覆盖审计

递进学习入口：Day31～32 看 `step01`，Day33～34 看 `step02`，Day35～36 看 `step03`，Day37～38 看 `step04`，Day39～40 看 `step05`；`production_graph.py` 是最终合并结果。

| 原文件能力 | 新项目位置 | 验收方式 |
|---|---|---|
| Day31 try/except fallback | `specialist`、`UnavailableAdapter` | 适配器抛永久错误后 Graph 仍完成 |
| Day31 RetryPolicy | LLM 节点 `retry_policy` | 瞬时异常重试，确定错误不重试 |
| Day31 ToolNode 错误回喂 | specialist 把错误写入 `errors` 后回 supervisor | 单专家失败不崩全图 |
| Day31 timeout | `call_with_timeout` + SDK timeout | 超时后降级，不无限等待 |
| Day32 枚举 Supervisor | `RouteDecision`、`QualityDecision` | Pydantic parse 失败则节点失败，不猜字符串 |
| Day32 意图分类 | intent + sources | public_info/family_data/calculation/chitchat 可断言 |
| Day32 业务可执行性 | in_scope + missing_information | 越界请求终止，信息不足进入 clarify |
| Day33 Plan-and-Execute | `WorkItem`、completed_items、supervisor | 不同 group 顺序执行 |
| Day33 五类范式 | README 学习顺序与架构说明 | 能解释本图为何混合 Plan/ReWOO/Reflexion |
| Day34 updates/values/messages/debug | `run_online --stream-mode` | 四种模式均可运行 |
| Day34 JSONL/LangSmith | trace 文件 + LangChain tracing | 节点耗时与模型调用树可查 |
| Day35 checkpoint/thread | `open_checkpointer` | memory/sqlite 可选 |
| Day35 trim/summary | manage_context | 完整历史与模型视图分离 |
| Day36 streaming | runner | 运行中持续看到事件 |
| Day36 HITL | approval + Command | 在线终端 approve/reject |
| Day37 Tavily/ReAct/轨迹 | Tavily adapter + specialist + trace | 真实 URL 进入 evidence |
| Day38 生成/校验/执行/解释 SQL | DeepSeekGateway + SafeSqlAdapter + generate | SQL、rows、自然语言答案均保留 |
| Day39 Supervisor | supervisor 循环 | 每批专家完成后回主管 |
| Day39 fan-out/fan-in/reducer | Send + Annotated reducers | web/sql/mcp 同组并行汇聚 |
| Day39 agent-as-tool | specialist/MCP 子 Agent 独立上下文 | 主 state 不包含子 Agent 中间消息 |
| Day40 Tools | MCP create_agent | 实际调用月供/能源费/TCO 工具 |
| Day40 Resources | resource_requests | car-decision-rules 进入 evidence |
| Day40 Prompts | prompt_requests | car_purchase_analysis 进入 evidence |
| Day40 stdio/HTTP/多 Server/鉴权 | build_online_services | 环境变量切换、业务图不改 |
