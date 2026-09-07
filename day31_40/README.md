# Day31～40 完整项目：家庭购车决策 Copilot

Day28～30 已经解决了“怎样创建图、怎样分支、怎样让 Agent 调工具”。这组项目解决下一个问题：

> 一个能跑的 Graph，为什么通常还不能给真实用户使用？一次可靠生成究竟经历了什么？

整个项目只讲一个容易理解的业务实例：

> 用户录入自己真实的预算、通勤、年里程和充电条件。
> Copilot 搜索真实候选车型的最新公开资料，查询已录入的家庭画像与核验数据，
> 用 MCP 计算月供、年度能源费和五年总持有成本，生成经过质量审核与家庭成员批准的购车建议报告。

这里的“发布”只表示采纳/保存报告，系统不会自动下单、申请贷款或付款。项目不再预置家庭或车型样例；
候选车型必须带来源 URL 和核验时间，价格、政策、安全和质保等时效信息必须在线搜索并保留 URL。

主程序默认走真实在线服务，不会自动切换成假模型或假搜索：

- DeepSeek：结构化路由、计划、Text2SQL、草稿生成、质量审核、重新规划、历史摘要。
- Tavily：真实互联网搜索，返回摘要和 URL。
- SQLite：真实数据库；只读查询用户明确录入的家庭画像与已核验候选车数据。
- MCP：由 `production_graph.py --mcp-server` 提供，计算月供、能源费、五年 TCO 和预算占比，并读取 Resources/Prompts。
- `adapters.py`、`car_mcp_server.py`、`run_online.py`、`configure_real_data.py` 现在只是兼容转发层，真正实现集中在 `production_graph.py`。

测试中的 fake 只用于快速验证 Graph 的确定性边界，不是主程序的降级模型。

## 0. 不要直接从最终版开始

`production_graph.py` 是 Day40 完成后的最终成品，不是第一份阅读材料。学习时按五个递进版本走：

| 阶段 | 对应日期 | 文件 | 本次只新增什么 |
|---|---|---|---|
| Step 1 | Day31～32 | `step01_reliable_routing.py` | 请求能否执行：校验、追问、越界、受限动作、真实搜索与重试 |
| Step 2 | Day33～34 | `step02_planning_observability.py` | 多维度比较：计划、cursor、执行循环、stream、JSONL |
| Step 3 | Day35～36 | `step03_persistence_hitl.py` | 家庭多轮讨论：历史摘要、checkpoint、报告确认与恢复 |
| Step 4 | Day37～38 | `step04_evidence_generation.py` | 真实证据：Tavily、已录入数据、安全 Text2SQL、证据生成 |
| Step 5 | Day39～40 | `step05_supervisor_mcp.py` | 多来源与依赖：Supervisor、Send、Reducer、MCP 成本计算 |
| Final | 综合加固 | `production_graph.py` | 安全、租户、幂等、预算、质量与重规划闭环 |

每一步都能独立运行。理解当前 Step 的 State、节点和边以后再进入下一步。

五个文件统一使用最终版命名，不再使用 `Step02State`、`StepRoute` 这类临时类型：

| 固定名称 | 从哪一步出现 | 到最终版发生什么变化 |
|---|---|---|
| `GraphState` | Step1 | 后续只增加字段，名字不变 |
| `RouteDecision` | Step1 | 始终表示结构化路由结果 |
| `WorkItem` | Step2 | Step4 接真实数据源，Step5 增加并行组 |
| `Evidence` | Step1 | 从真实 Web URL 扩展为 Web/SQL/MCP 统一证据 |
| `ModelGateway` | Step1 | 后续逐渐增加 plan、SQL、summary 等能力 |
| `build_graph()` | Step1 | 每个阶段都用相同构图入口 |
| `initial_state()` | Step1 | 字段随能力增加，但入口名字不变 |

节点名称也保持同一语义：`specialist` 在 Step1 调真实搜索，Step2 执行计划步骤，Step4 增加安全 SQL，Step5 变成并行 Web/SQL/MCP 专家；最终版仍叫 `specialist`。`compose_context` 和 `generate` 也沿用同一名称。

这些 Step 是五个“可独立运行的能力切片”，最终版把切片接到同一张图上；它们不是五份需要复制粘贴的完整项目快照。

## 1. 先看完整 Graph

```text
START
  ↓
intake ─────────────── 输入长度、tenant_id、request_id、幂等键
  ↓
manage_context ─────── 完整历史保留；摘要 + 最近 4 轮作为模型视图
  ↓
safety_gate ────────── PII 脱敏、提示注入检测
  ├─ 拦截 → blocked_answer → publish → END
  ↓
route ──────────────── 结构化选择 public_info/family_data/calculation/chitchat
  ├─ 缺必要信息 → clarify → publish → END
  ├─ 非购车请求 → out_of_scope → publish → END
  ↓ 可执行
plan ───────────────── 生成带 id、source、parallel_group 的任务清单
  ↓
supervisor ◄──────────────────────────────────────────┐
  │                                                   │
  ├─ 同组任务 → specialist(web/sql/mcp) fan-out ─────┘
  │                每个专家独立上下文，只返回证据摘要
  ↓ 全部完成或预算耗尽
compose_context ────── 将异构工具结果变成 [1][2] 编号证据
  ↓
generate ───────────── 问题 + 历史视图 + 证据 + 上轮反馈 → 草稿
  ↓
quality_gate ───────── 独立审校：事实、引用、相关性、不确定性
  ├─ 缺证据 → replan → supervisor
  ├─ 表达差 → revise → generate
  └─ 通过/达到护栏
  ↓
approval ───────────── 高风险动作或临界质量 → interrupt 等人工
  ↓
publish ────────────── 幂等发布、写入对话历史
  ↓
END
```

最重要的认识：**生产生成不是一次 `llm.invoke()`。** 模型生成的只是 `draft`，最终结果还取决于证据、质量门禁、修订上限和人工审批。

## 2. 新人应该怎样读状态

不要从头背代码。先跟踪这些字段：

| 字段 | 它回答的问题 |
|---|---|
| `route` | 请求是否属于购车范围、缺什么信息、为什么选择 Web/SQL/MCP？ |
| `work_items` | 总任务被拆成了哪些可执行步骤？哪些能并行？ |
| `completed_items` | Supervisor 已经收回了哪些专家结果？ |
| `evidence` | 外部系统实际返回了什么？有无降级警告？ |
| `context` | 异构结果怎样变成模型可引用的统一证据？ |
| `draft` | 模型基于哪些输入生成了什么？ |
| `quality` | 为什么通过、修订、补证据或转人工？ |
| `trace` / `errors` | 哪个节点失败、降级或变慢？ |
| `approval_status` | 外部副作用是否得到人类授权？ |
| `conversation_history` / `history_summary` | 审计全量历史与模型实际看到的视图有何不同？ |

## 3. Day31～40 已合并的全部能力

### Day31：可靠性不是 `try/except` 一个词

- Graph 的 LLM 节点使用 `RetryPolicy`，只重试 `TimeoutError/ConnectionError`。
- 搜索、SQL、MCP 适配器使用真实超时、指数退避和最大尝试次数。
- 参数、权限、SQL 安全错误属于永久错误，快速失败，不浪费重试。
- 专家错误会写入 `errors` 并返回 Supervisor，等价于工具错误回喂，不拖垮整图。
- 重试耗尽后只返回“数据源不可用”，绝不伪造搜索或业务数据。

### Day32：路由输出必须能被程序可靠消费

- `RouteDecision` 约束 intent、sources、requires_approval。
- `QualityDecision` 只能选择 pass/revise/replan/human_review。
- 使用 `PydanticOutputParser`，兼容 OpenAI-compatible 模型。
- 分类后真正分到知识、结构化数据、外部动作或闲聊路径，而非关键词控制边。

### Day33：Plan-and-Execute、ReWOO 和重新规划

- `WorkItem` 是显式计划，不是一段自由文本。
- `parallel_group` 相同的任务并行执行，不同组顺序推进。
- `completed_items` 相当于原来的 cursor/done，支持 checkpoint 后恢复。
- 质量门禁发现缺证据时走 `replan`，而不是拿错误计划反复重写。
- ReAct、Plan-and-Execute、ReWOO 的取舍见下方学习顺序。

### Day34：必须能看见每一步

- `trace` 记录节点、说明、耗时和时间戳。
- 在线入口支持 `updates`、`values`、`messages`、`debug` 四种 stream mode。
- 每次运行写 JSONL，并截断超长内容，避免日志无限增长。
- 设置 LangSmith 环境变量后，LangChain 模型调用会进入 LangSmith 调用树。

### Day35：checkpoint 不等于无限上下文

- checkpointer 按 `thread_id` 保存每个 super-step。
- `conversation_history` 保存完整历史，用于审计和恢复。
- `history_summary + recent_history` 才是模型实际看到的压缩视图。
- 历史只摘要一次，通过 `history_summarized_count` 避免每轮重复烧 Token。
- 支持 InMemorySaver 和 SqliteSaver；多实例生产应注入 PostgresSaver。

### Day36：streaming 和 HITL

- 长任务可持续输出节点更新或模型消息。
- 发布、发送、付款、删除、写入等动作由路由标记 `requires_approval`。
- `interrupt()` 把草稿、质量和风险信息交给审批者。
- `Command(resume="approve"/"reject")` 从 checkpoint 恢复；审批服务无需与运行进程相同。

### Day37：真实搜索 Agent

- Tavily 返回真实摘要与 URL。
- 每条内容限长，避免搜索结果把上下文窗口挤爆。
- 搜索有连接时限、重试、降级和来源保留。
- 搜索专家只返回证据，不直接决定最终答案。

### Day38：真实 Text2SQL

```text
自然语言 → DeepSeek 生成 SQL → 确定性安全校验 → SQLite 只读连接 → rows + SQL 进入证据
```

安全门包含：SELECT/只读 CTE、单语句、禁止注释、危险关键字、表白名单、强制 LIMIT 100。数据库连接再执行 `PRAGMA query_only=ON`，形成纵深防御。

### Day39：Supervisor、fan-out/fan-in、agent-as-tool

- Supervisor 循环检查未完成计划，按 `parallel_group` 派发下一批专家。
- `Send` 实现动态 fan-out，Reducer 合并 evidence、completed_items、trace 和 errors。
- Web/SQL/MCP 专家只收到一条 instruction，不共享完整主状态。
- MCP 内部的工具 Agent 也是独立上下文，主 Graph 只收到摘要。
- `max_supervisor_steps`、`max_tool_calls`、`recursion_limit` 三层防死循环。

### Day40：MCP 三种原语和两种传输

- Tools：月供、年度能源费、五年 TCO、预算占比等确定性计算。
- Resources：读取 `config://car-decision-rules` 作为报告边界。
- Prompts：读取服务端 `car_purchase_analysis` 团队模板。
- 默认通过 stdio 启动本地购车计算 Server。
- 设置 `MCP_CAR_REMOTE_URL` 后可同时连接远程 streamable-http Server。
- stdio 使用 env 注入认证；HTTP 使用 headers。

## 4. 原十天之外已经补上的生产问题

| 扩展 | 为什么必须补 | 当前实现 |
|---|---|---|
| Prompt Injection | 外部工具和系统提示词不能被用户绕过 | `safety_gate` 在 LLM 前确定性拦截 |
| PII | 电话、邮箱不应直接进入模型和轨迹 | 输入脱敏并记录 `pii_redacted` |
| 多租户隔离 | checkpoint 串租户会造成数据泄露 | tenant 必填，runner 强制 thread_id 前缀 |
| 幂等 | 审批恢复或网络重试不能重复发布 | `idempotency_key` + `published_keys` |
| 预算/收敛 | Supervisor 和反思循环可能无限烧 Token | 工具、主管、修订、重规划四种上限 |
| Grounding | 文风好不代表事实正确 | 证据编号 + 独立质量 Agent + replan |

## 5. 在线环境配置

安装基础依赖后再安装本项目在线依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r day31_40\requirements-online.txt
```

`.env` 至少配置：

```dotenv
DEEPSEEK_API_KEY=你的真实Key
TAVILY_API_KEY=你的真实Key

# 可选
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
LLM_TIMEOUT_SECONDS=30
SEARCH_TIMEOUT_SECONDS=10
DEMO_TOKEN=secret-123
MCP_CAR_REMOTE_URL=http://127.0.0.1:8000/mcp
MCP_AUTH_TOKEN=xxx
```

`MCP_CAR_REMOTE_URL` 是可选的远程服务地址；默认本地 stdio 服务不需要手工启动。

## 6. 真实运行与调试

先录入你自己的家庭画像。下面的尖括号内容必须替换成真实值：

```powershell
.\.venv\Scripts\python.exe day31_40\production_graph.py profile `
  --family-name "<家庭名称>" --purchase-budget <购车总预算> `
  --available-cash <可用现金> --monthly-payment-limit <月供上限> `
  --annual-mileage <真实年里程> --daily-commute <真实通勤公里> `
  --passengers <常用乘员数> --home-charger yes
```

再录入已经通过官网、经销商书面报价或其他可信来源核验的真实候选车型：

```powershell
.\.venv\Scripts\python.exe day31_40\production_graph.py car `
  --name "<品牌车型和配置>" --powertrain bev --price <核验价格> `
  --energy-use <核验百公里能耗> --energy-unit kWh `
  --insurance <真实保险估算> --maintenance <真实年度保养估算> `
  --resale-value-5y <五年残值估算> --source-url "<可追溯URL>"
```

数据库为空时 SQL 会真实返回空结果，Graph 必须披露缺少数据，不会自动补造车型。

同时触发搜索、SQL 和 MCP：

```powershell
.\.venv\Scripts\python.exe day31_40\production_graph.py run `
  "请读取我已录入的家庭画像和真实候选车，在线核验最新资料，用MCP计算月供、年度能源费和五年总持有成本，最后生成带引用的购车建议报告" `
  --tenant family-user `
  --thread family-user:car-decision `
  --stream-mode updates
```

观察完整 state：

```powershell
.\.venv\Scripts\python.exe day31_40\production_graph.py run "你的问题" --stream-mode values
```

观察模型消息/Token：

```powershell
.\.venv\Scripts\python.exe day31_40\production_graph.py run "你的问题" --stream-mode messages
```

观察底层调度事件：

```powershell
.\.venv\Scripts\python.exe day31_40\production_graph.py run "你的问题" --stream-mode debug
```

持久化 checkpoint：

```powershell
.\.venv\Scripts\python.exe day31_40\production_graph.py run "请搜索资料并发布总结" `
  --checkpoint sqlite --thread family-user:approval
```

## 7. 两套测试，不要混为一谈

快速 Graph 回归测试不调用外部服务：

```powershell
.\.venv\Scripts\python.exe -m pytest day31_40\tests\test_production_graph.py -q
```

真实在线验收会消耗 DeepSeek/Tavily 额度，并真实启动 MCP Server：

```powershell
.\.venv\Scripts\python.exe -m pytest day31_40\tests\test_online_graph.py `
  --run-online -m online -s
```

在线测试要求 web/sql/mcp 三类真实证据全部出现，而且禁止 `unavailable://` 降级结果混过验收。

## 8. 建议的新人学习顺序

### 第一次：Step 1

```powershell
.\.venv\Scripts\python.exe -m day31_40.step01_reliable_routing
```

分别输入“想买车但没有预算信息”“软件开发问题”“查询最新质保”和“帮我付款”，观察
`route` 怎样进入 `clarify/out_of_scope/specialist/restricted_action`；再断开网络观察瞬时错误重试。

### 第二次：Step 2

```powershell
.\.venv\Scripts\python.exe -m day31_40.step02_planning_observability
```

跟踪 `work_items/completed_items/trace`，确认为什么多维度购车比较需要逐项执行、循环何时结束；
本步只生成待取证计划，不把模型输出冒充真实车型资料。

### 第三次：Step 3

```powershell
.\.venv\Scripts\python.exe -m day31_40.step03_persistence_hitl
```

亲自 approve/reject 一份家庭购车需求确认稿，理解 `publish` 只保存报告、不执行交易；
同时理解执行位置保存在 checkpoint，而不是 Python 进程卡在节点里。

### 第四次：Step 4

```powershell
.\.venv\Scripts\python.exe -m day31_40.step04_evidence_generation
```

观察 Tavily 结果和 SQL rows 怎样统一成 `[1][2]` 上下文；临时让 SQL 生成器返回 DELETE，确认安全门在数据库执行前拒绝。

### 第五次：Step 5

```powershell
.\.venv\Scripts\python.exe -m day31_40.step05_supervisor_mcp
```

对比同一 parallel_group 与不同 group，观察 fan-out 和顺序批次；再查看 MCP Tools、Resources、Prompts 如何只通过适配器进入 Graph。

### 最后：生产加固版

完成五步以后再阅读 `production_graph.py`，重点比较它比 Step5 多出的 safety、context、quality、replan、approval、idempotency 和 budget 节点。

## 9. 仍然不能冒充“真实购车交易平台”的部分

这张图已经完整覆盖 Day31～40，并补齐核心生产护栏，但真实上线还需要后续章节继续建设：

- OAuth/JWT、RBAC、工具级权限与审批人权限校验。
- Redis 限流、缓存、熔断器、分布式锁和任务队列。
- Token/费用精确核算、模型路由和租户配额。
- Postgres checkpoint、备份恢复、状态 schema 迁移和数据保留策略。
- 搜索网页抓取防间接提示注入、文档 ACL 和引用内容一致性校验。
- Prompt/模型/工具版本化，离线评测集、在线反馈、回归门禁与告警 SLO。
- 异步 Graph、取消传播、Webhook、长任务后台执行和水平扩容。

这些不应该继续无限塞进 Day31～40，否则新人会失去主线；它们适合作为 Day41 之后的服务化、测试、安全和部署阶段。
