# Day31–Day40 详细章节概括：让 Agent 可控、可查、可暂停，并接入外部工具

这一组的主线是：先给 Agent 加错误处理和可靠路由，再加入规划、观测、持久化、人工审批，最后把搜索、Text2SQL、多 Agent 和 MCP 串起来。

## Day31 · 节点容错、重试和超时

代码在：[day31/day31_node_reliability.py](../day31/day31_node_reliability.py)

Day31 做的事情是：**解决 Day30 的 Agent 一旦工具或节点报错，整张图直接崩掉的问题。**

### 1. 节点级 fallback

```python
try:
    result = risky_node(state)
except Exception:
    return {"answer": "暂时无法完成，请稍后重试"}
```

捕获异常后返回一个可识别的降级结果，让图继续走，而不是裸奔成 HTTP 500。

### 2. 只对瞬时错误重试

```text
网络抖动、429、短暂超时 → 可以有限重试
参数错误、无权限、业务拒绝 → 不应反复重试
```

代码使用 `RetryPolicy` 演示节点级重试。重试次数必须有上限，否则一个坏节点会把整个请求拖很久。

### 3. 工具错误和超时也要进入流程

工具抛错时，可以把异常转成 `ToolMessage` 交回模型，让模型换一个策略；慢节点则需要超时护栏，防止一个卡死的工具占满整个请求。

### 4. Day31 最终要记住什么？

> 可靠性不是“所有异常都吞掉”，而是区分可重试、可降级和必须快速失败的错误。

## Day32 · 用结构化输出做可靠路由

代码在：[day32/day32_structured_routing.py](../day32/day32_structured_routing.py)

Day32 做的事情是：**解决用自由文本关键词判断下一步，导致 Agent 路由不稳定的问题。**

### 1. 为什么字符串路由危险？

```python
if "RESEARCH" in last.content:
    goto("research")
```

模型可能输出：“我建议先 RESEARCH，再 WRITING”，这样两个关键词都命中，程序就不知道该走哪条路。自由文本适合给人看，不适合直接控制流程。

### 2. 定义有限的路由 schema

```python
class Route(BaseModel):
    next: Literal["research", "writing", "finish"]
```

再用 `PydanticOutputParser` 给模型注入格式要求：

```text
模型只能从枚举值中选择一个 next
  → parser 解析
  → 路由函数读取 route.next
```

### 3. 用在客服意图分流

用户问题可以先分类：

```text
查询 → 知识库/订单查询
投诉 → 工单/人工升级
闲聊 → 普通聊天
```

这和后面的 Text2SQL、RAG、多 Agent supervisor 都是同一种模式：先可靠识别意图，再把请求交给正确分支。

### 4. Day32 最终要记住什么？

> 只要模型输出会决定程序走哪条路，就应该把它约束成枚举或结构化字段，而不是用 `in` 猜意图。

## Day33 · Plan-and-Execute 规划范式

代码在：[day33/day33_plan_and_execute.py](../day33/day33_plan_and_execute.py)

Day33 做的事情是：**先了解主流 Agent 规划方式，再实现“先计划、后执行”的 Agent。**

### 1. 先区分几种范式

```text
ReAct             → 边思考边行动
Plan-and-Execute  → 先生成计划，再逐步执行
Reflexion         → 行动后反思并改进
ReWOO             → 先规划工具调用，减少中间上下文
Tree of Thoughts  → 探索多条思路再选择
```

这里不是要全部实现，而是建立“不同任务应该选不同流程”的判断能力。

### 2. 实现 Plan-and-Execute

```text
用户任务
  → planner 生成有序步骤
  → executor 执行当前步骤
  → 更新 state，划掉已完成步骤
  → 还有步骤？继续；没有？结束
```

计划显式保存在 state 中，因此更容易审计、展示和在失败后恢复。

### 3. Day33 最终要记住什么？

> ReAct 更灵活，Plan-and-Execute 更显式可控。选择 Agent 范式要看任务是否需要稳定步骤、人工审查和过程审计。

## Day34 · Agent 可观测性和调试

代码在：[day34/day34_observability.py](../day34/day34_observability.py)

Day34 做的事情是：**让 Agent 每一步都看得见、能落盘、能复盘。**

### 1. 四种 stream 视角

```text
updates  → 当前节点更新了哪些 state 字段
values   → 每一步之后完整 state
messages → 消息/Token 流
debug    → 节点进出、耗时等最详细信息
```

调试流程通常先看 `updates`，需要完整快照时看 `values`，需要用户打字机效果时看 `messages`。

### 2. 把轨迹写成 JSONL

```json
{"node":"retrieve","latency_ms":42,"output":"3 docs"}
{"node":"generate","latency_ms":830,"output":"answer"}
```

一行一条事件，比散落的 `print` 更容易 grep、按请求回放和做回归比较。

### 3. Day34 最终要记住什么？

> Agent 出问题时要能回答“哪一步、耗时多少、输入输出是什么”。没有结构化轨迹，就很难定位模型、检索或工具层的问题。

## Day35 · Checkpoint 持久化和上下文管理

代码在：[day35/day35_checkpoint_context.py](../day35/day35_checkpoint_context.py)

Day35 做的事情是：**让 LangGraph 的状态可以按 thread 保存和恢复，同时控制长对话的上下文成本。**

### 1. 用 checkpointer 保存 state 快照

```python
checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "user-001"}}
```

同一个 `thread_id` 可以继续上一轮对话，也可以从中断位置恢复；不同 thread 用于隔离不同用户。

### 2. checkpoint 能解决什么？

```text
多轮记忆       → 继续携带历史
中断恢复       → 从上次节点继续
多用户隔离     → thread_id 分开保存
```

`InMemorySaver` 重启会丢数据，生产应换 SQLite 或 Postgres checkpointer。

### 3. 长上下文不能无限增长

常见策略是：

```text
保留最近 N 轮原文
更早历史压缩成摘要
摘要中保留用户身份、订单号、关键事实
```

上下文工程的目标不是盲目保留更多，而是在成本、窗口和事实完整性之间平衡。

### 4. Day35 最终要记住什么？

> checkpoint 保存的是应用流程状态，不是模型突然拥有永久记忆；长期运行还要设计存储、隔离、摘要和恢复策略。

## Day36 · 流式中间步骤和人工确认

代码在：[day36/day36_streaming_hitl.py](../day36/day36_streaming_hitl.py)

Day36 做的事情是：**让用户看到 Agent 的中间进展，并在高风险动作前暂停等待人工确认。**

### 1. 流式输出不只流最终文字

```python
for event in app.stream(input_state, config):
    print(event)
```

它可以展示“已经走到哪个节点、state 怎么变、工具是否执行”，同时改善长任务的等待体验。

### 2. 用 `interrupt()` 暂停危险操作

```python
decision = interrupt({
    "action": "delete",
    "target": state["target"],
    "ask": "确认删除吗？回复 yes / no",
})
```

图在这里暂停，人工确认后用 `Command` 恢复；拒绝则取消动作。

### 3. 哪些动作必须人工确认？

```text
删除数据、付款、发邮件、修改权限、提交生产变更
```

这些动作具有外部副作用，不能因为模型“觉得应该做”就直接执行。

### 4. Day36 最终要记住什么？

> streaming 解决体验，HITL 解决副作用安全；人工审批依赖 checkpoint 的暂停和恢复能力。

## Day37 · 搜索+总结 Agent 综合项目

代码在：[day37/day37_tool_safety_search.py](../day37/day37_tool_safety_search.py)

Day37 做的事情是：**把 Day30–Day36 的能力合成一个能讲、能演示、能审计的搜索总结 Agent。**

### 1. 第一条主链：搜索、循环和总结

```text
用户任务
  → 搜索工具
  → ReAct 判断是否继续搜索
  → 汇总搜索结果
  → 生成总结
```

每一步都记录轨迹，出错时可以知道搜索了什么、模型为什么继续或停止。

### 2. 第二条主链：持久化和人工采纳

```text
thread_id 保存会话
  → 生成答案
  → interrupt 等人审核
  → approve 后才采纳
```

联网搜索包或 API 不可用时，代码用内置假数据保证流程仍可运行，重点是理解编排和安全边界。

### 3. Day37 最终要记住什么？

> 一个可用 Agent 不只要会调用工具，还要能记住上下文、记录轨迹，并在最终结果产生业务影响前让人把关。

## Day38 · Text2SQL：让 Agent 查询结构化数据

代码在：[day38/day38_text2sql_agent.py](../day38/day38_text2sql_agent.py)

Day38 做的事情是：**给 Agent 增加一个结构化数据分支，让自然语言问题可以查询 SQLite。**

### 1. Text2SQL 的基本链路

```text
自然语言问题
  → 生成只读 SQL
  → 校验 SQL
  → 查询 SQLite
  → 把 rows 解释成自然语言
```

它适合订单、销售、财务和评测记录等表格数据；RAG 更适合非结构化文档，两者是互补分支。

### 2. 代码的安全边界

```python
ALLOWED_TABLES = {"sales", "conversations"}
DANGEROUS = {
    "insert", "update", "delete", "drop", "alter",
    "create", "replace", "attach", "detach", "pragma",
}
```

只允许白名单表，只允许 `SELECT`，拒绝写操作关键字，并自动增加 `LIMIT`，防止模型生成一次查全库的危险语句。

### 3. 为什么要返回实际 SQL？

```python
@dataclass
class QueryResult:
    sql: str
    rows: list[dict]
    answer: str
```

保留 `sql` 方便审计和调试，保留原始 `rows` 方便判断自然语言解释是否忠实。

### 4. Day38 最终要记住什么？

> Text2SQL 的核心不是“让模型写 SQL”，而是让模型生成的 SQL 进入白名单、只读、限量、可审计的执行边界。

## Day39 · Supervisor、多 Agent 和 fan-out

代码在：[day39/day39_langgraph_supervisor.py](../day39/day39_langgraph_supervisor.py)

Day39 做的事情是：**把一个 Agent 扛不住的复合任务拆给多个专家，再由 Supervisor 协调。**

### 1. Supervisor 模式

```text
supervisor
  → research 专家
  → supervisor
  → writing 专家
  → supervisor
  → review 专家
  → FINISH
```

Supervisor 根据当前 state 决定下一步交给谁，专家完成工作后回到主管。代码还设置 `max_steps` 防止主管路由死循环。

### 2. fan-out / fan-in 并行

```text
一个任务
  ├─ 分支 A：查产品资料
  ├─ 分支 B：查用户反馈
  └─ 分支 C：查竞品信息
           ↓
         汇聚总结
```

独立分支可以并行执行，减少总耗时；汇聚时必须用正确 reducer，避免结果互相覆盖。

### 3. agent-as-tool

子 Agent 也可以不作为图节点，而是作为主 Agent 的一个工具。它独立拥有上下文，主 Agent 只收到任务结果摘要，这样可以节省主上下文空间。

### 4. Day39 最终要记住什么？

> 多 Agent 的价值是分工、上下文隔离和并行，不是简单地把模型调用次数变多。

## Day40 · MCP：用标准协议接入外部工具

代码在：[day40/day40_mcp_agent.py](../day40/day40_mcp_agent.py)

Day40 做的事情是：**把写死在 Python 代码里的 `@tool`，升级成由外部 MCP Server 按标准协议提供的工具和数据。**

### 1. MCP 客户端连接 Server

```python
client = MultiServerMCPClient({
    "local": {"command": "python", "args": ["server.py"]},
    "remote": {"url": "http://127.0.0.1:8000/mcp"},
})
tools = await client.get_tools()
agent = create_agent(model=get_llm(), tools=tools)
```

客户端可以连接本地 stdio 服务，也可以连接远程 HTTP 服务；工具由 Server 提供，Agent 端不需要重新实现每个函数。

### 2. MCP 不只有 Tools

代码还演示：

```text
Tools     → 可调用动作
Resources → 只读数据，作为上下文
Prompts   → 团队沉淀的可复用问法
```

还可以同时挂载多个 MCP Server，用统一方式把外部系统接入 Agent。

### 3. Day40 最终要记住什么？

```text
Agent      → 决定如何思考和行动
LangGraph  → 编排状态、分支和循环
MCP        → 标准化连接外部工具和数据
```

MCP 不是 Agent 框架，也不是 RAG 框架，而是连接层。

## Day31–Day40 总结：这一组到底把 Agent 变成了什么？

```text
错误处理
  → 结构化路由
  → 规划执行
  → 轨迹观测
  → checkpoint / 上下文
  → 流式 + 人工审批
  → 搜索 Agent
  → Text2SQL
  → 多 Agent
  → MCP 外部工具
```

Day40 结束时，Agent 已经不只是“模型加几个工具”，而是一个有状态、有流程、有安全边界、有观测能力、能连接外部系统的应用框架。
