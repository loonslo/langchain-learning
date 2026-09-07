# Day91–Day100 详细章节概括：把客服 Agent 从对话契约推进到可交付基础设施

这一组承接 Day90 的 few-shot 意图契约：先把多轮对话里的缺参、结构化输出和人工转接变成显式规则，再把会话、数据库、缓存、向量检索和模型服务接到可以本地复现的工程边界。它仍然是企业客服 Agent 的进阶骨架，不等于已经完成生产高可用部署。

## Day91 · 槽位抽取与缺参追问

说明在：[day91/README.md](../day91/README.md)

Day91 做的事情是：**把 Day90 识别出的意图补成可执行的槽位状态，只在缺少必要业务字段时追问。** 例如退款进度和订单状态需要 `order_id`，而配送咨询不需要订单号。

### 1. 槽位处理链路

```text
当前意图 + 本轮问题 + 上轮槽位
  → extract_slots
  → 合并已有字段
  → 计算 missing
  → SlotState
  → next_question
```

`extract_slots` 只识别带有“订单号”或 `order id` 标记的确定格式，并统一转成大写；没有匹配到就不把猜测出的号码写进会话。跨轮对话中，上一轮保存的字段会和本轮新抽取的字段合并。

### 2. 哪些意图需要什么？

```text
refund_status → order_id
order_status  → order_id
shipping      → 不需要槽位
human_handoff → 不需要槽位
unknown       → 不需要槽位
```

如果 `missing` 不为空，只返回第一个必要字段的提示，例如“请提供订单号，我再为你查询”；字段齐全时不再追问，并返回完整的 `SlotState`。

### 3. Day91 的边界

这里的规则抽取是可测试基线，不代表模型已经能可靠理解所有自然语言。上线时可以替换成 LLM schema 抽取，但仍应复用 `SlotState` 契约和缺参校验，不能让模型自行决定业务字段是否足够。

### 4. Day91 最终要记住什么？

> 意图只说明要走哪条业务线；槽位状态才说明这条业务线是否已经拿到可以执行的输入。

## Day92 · 大模型稳定输出 JSON

说明在：[day92/README.md](../day92/README.md)

Day92 做的事情是：**把模型文本收敛成可以审计的 JSON 契约，格式不对时最多进行一次受控修复。** “提示模型返回 JSON”并不等于可以把文本直接交给 `json.loads()`。

### 1. 从模型文本到业务对象

```text
模型文本
  → 提取完整 JSON 对象
  → JsonSchema 校验
  → 保留声明字段
  → 进入业务
```

完整的 fenced JSON 可以被提取，但前后夹杂说明文字的输出会被拒绝。结果必须是对象，不能是数组或字符串；缺少声明字段、出现额外字段，都会触发 `StructuredOutputError`。

### 2. 类型也要严格检查

```text
字段存在性
字段白名单
字段精确类型
bool 与 int 区分
```

`JsonSchema` 默认不允许额外字段，并且用精确类型检查，避免 Python 里 `bool` 是 `int` 子类导致业务 JSON 被误判为合法。

### 3. 一次修复，不做无限重试

```text
原始输出
  → 校验失败？
  → repair(text) 一次
  → 再次校验
  → 成功返回 / 汇总错误后失败
```

`parse_model_json` 最多尝试原始文本和一次修复结果。修复器本身也是一次模型调用，需要计入成本、trace 和失败率；不能写成“重试到能解析为止”的无边界循环。

### 4. Day92 最终要记住什么？

> 稳定 JSON 的核心不是让模型永远不犯错，而是让错误在进入业务前有明确的拒绝和有限修复边界。

## Day93 · 客服意图、槽位与人工转接工作流

说明在：[day93/README.md](../day93/README.md)

Day93 做的事情是：**把意图契约、槽位状态和人工转接接成一个显式会话状态机。** 这一步解决的是“知道要做什么，却不知道当前输入够不够，以及不确定时该怎么退出”的问题。

### 1. 一次请求如何分支？

```text
handle(session_id, question)
  → 有待补槽位？复用上轮意图
  → 否则调用 IntentClassifier
  → unknown 或 confidence < 0.75？转人工
  → 明确 human_handoff？转人工
  → 缺槽位？保存状态并追问
  → 槽位齐全？清理状态并返回 ready
```

如果会话正在等待订单号，下一轮不会重新猜意图，而是沿用上轮意图并继续补参。低置信度或未知意图会清理会话状态，返回 `handoff`；槽位不全返回 `needs_slot`；信息齐全返回 `ready`。

### 2. 状态和输出是显式的

```text
ConversationState
  → session_id : SlotState
  → SupportReply(text, status, intent, slots)
```

业务入口不靠模型自由决定下一步，而是根据 `SupportReply.status` 进入追问、人工转接或后续受控处理。状态齐全后才允许接订单、退款或知识库能力。

### 3. Day93 的边界

当前 `ConversationState` 是教学用内存实现，生产需要替换成带租户和用户边界的持久化仓储。退款、订单查询、发消息等有副作用的动作，还必须经过鉴权、只读查询或审批；显式工作流不等于让 Agent 自主执行一切。

### 4. Day93 最终要记住什么？

> 业务流程要把“继续、追问、转人工、进入后续处理”写成可检查的状态分支，而不是交给模型自行发挥。

## Day94 · PostgreSQL 真实会话层与租户边界

说明在：[day94/README.md](../day94/README.md)

Day94 做的事情是：**把共享会话从本地 SQLite 思路推进到 PostgreSQL，并把租户隔离落实到数据库策略。** 多副本服务需要一个共享的会话真相源，不能让每个进程各自保存一份内存状态。

### 1. 会话写入与读取链路

```text
tenant_id + user_id + session_id + message
  → set_config('app.tenant_id', tenant_id, true)
  → 参数化 INSERT / SELECT
  → PostgreSQL RLS 策略
  → commit 或返回 history
```

仓储在每次操作前设置事务本地的租户上下文，事务结束就清除，避免连接池把上一个租户带给下一个请求。插入和查询的值都通过参数传入，不能把用户内容拼进 SQL。

### 2. 数据库层的隔离规则

```text
conversation_messages
  → ENABLE ROW LEVEL SECURITY
  → FORCE ROW LEVEL SECURITY
  → tenant_id = current_setting('app.tenant_id', true)
```

表结构同时限制角色只能是 `user` 或 `assistant`，并建立按租户、用户、会话和时间排序的索引。历史查询的 `limit` 只能在 1–100 之间，返回结果会恢复为从旧到新的顺序。

### 3. Day94 的边界

应用层的 tenant 校验和数据库 RLS 都要保留；应用连接不能使用表 owner 或绕过 RLS 的角色。RLS 也不会替代连接池治理、迁移、备份、恢复演练和慢查询优化。

### 4. Day94 最终要记住什么？

> 租户隔离不能只写在业务代码里；数据库也要知道当前租户，并在查询层拒绝越界数据。

## Day95 · Agent 查 PostgreSQL：目录优先与执行计划门禁

说明在：[day95/README.md](../day95/README.md)

Day95 做的事情是：**不给 Agent 一条可以任意执行的自然语言到 SQL 通道，而是优先使用服务端查询目录；必要的动态查询也必须只读、限表、限范围。**

### 1. 目录查询优先

```text
query_id + roles
  → QueryCatalog.get
  → 查询存在？
  → 角色有交集？
  → 校验为只读 SQL
  → 返回可执行查询
```

未知 `query_id` 或当前角色无权使用时直接拒绝。目录中的 SQL 仍会经过 `validate_read_only_sql`，避免“目录里写错了”就绕过底线。

### 2. 动态 SQL 的安全底线

```text
只允许 SELECT / 只读 WITH
禁止多语句和注释
禁止写操作、锁、执行和危险关键字
表名必须在白名单
必须显式 LIMIT
```

关键字、表名和查询形状会被检查，CTE 不能用来绕过只读规则。这样做是先把危险输入挡在数据库执行之前，而不是等 Agent 产生结果后再解释。

### 3. 执行计划门禁

```text
EXPLAIN (FORMAT JSON)
  → 遍历计划节点
  → Seq Scan 行数 > 100000？拒绝
  → 否则允许进入下一步
```

执行计划是最后一道成本保险，用来挡住明显的大范围顺序扫描。它不是索引设计的替代品；生产优化要结合真实慢查询、统计信息和受控的 `EXPLAIN ANALYZE`，不能对不可信 SQL 直接运行后者。

### 4. Day95 最终要记住什么？

> 让 Agent 查库的重点不是“能生成 SQL”，而是让查询来源、权限、读写范围和成本都能被程序拒绝或审查。

## Day96 · Redis：租户版本缓存与限流

说明在：[day96/README.md](../day96/README.md)

Day96 做的事情是：**把 Redis 放在热路径上做可失效缓存和请求协调，而不是把它当成会话数据库的替代品。**

### 1. 答案缓存键必须带上下文

```text
tenant_id
  + knowledge_version
  + acl_version
  + model
  + 规范化问题
  → JSON 排序后 SHA-256
  → answer:<hash>
```

问题会先合并空白，再和租户、知识版本、权限版本、模型一起生成键。知识同步、权限变化或模型切换后，版本变化会让旧键自然失效；缓存还有默认 300 秒 TTL。

### 2. 固定窗口限流

```text
tenant_id + user_id + window
  → Redis INCR
  → 首次计数设置过期时间
  → count <= limit 才允许
```

限流按租户、用户和窗口隔离。Redis 任意调用失败时会抛出“限流后端不可用”的 `RuntimeError`，按失败关闭处理，不能因为缓存服务故障就静默放开无限请求。

### 3. Day96 的边界

固定窗口可能产生边界突刺，生产可以换滑动窗口、令牌桶或网关限流，但故障时的失败关闭原则不能丢。Redis 缓存可以丢弃，租户权限和会话真相不能只放在 Redis。

### 4. Day96 最终要记住什么？

> 缓存命中必须受租户、权限、知识和模型版本约束；限流故障也必须被当成安全事件处理。

## Day97 · pgvector、Qdrant、Milvus 的选型与 Qdrant 适配器

说明在：[day97/README.md](../day97/README.md)

Day97 做的事情是：**把向量库选型写成可审查的规则，并让 Qdrant 查询始终带上服务端确定的租户过滤。** 选型不是背“哪家一定最好”，而是看现有数据库、过滤需求、规模和运维平台。

### 1. 选型依据

```text
超大规模 + Kubernetes 平台 → Milvus
需要关系事务 + 不想单独维护向量服务 → pgvector
需要过滤多租户或独立向量服务 → Qdrant
其他情况 → pgvector
```

`choose_vector_backend` 接收结构化的 `VectorRequirements`，返回 `PGVECTOR`、`QDRANT` 或 `MILVUS`。规则是显式的，后续可以用同一组 PoC 指标审查选择，而不是把业务代码绑死在某个 SDK。

### 2. Qdrant 查询的租户边界

```text
tenant_id + vector + limit
  → tenant_filter(tenant_id)
  → query_points(..., query_filter=...)
  → 返回带 payload 的结果
```

`tenant_id` 为空会直接报错，`limit` 只能在 1–50 之间。过滤器由适配器强制生成，调用者不能省略租户条件。

### 3. Day97 的边界

本阶段只实现了 Qdrant 适配器，Milvus 只完成选型和部署边界对比。若目标职位明确要求 Milvus，应保持 `VectorStore` 契约不变，补适配器，再用同一数据集比较召回、p95、写入、过滤和运维成本。

### 4. Day97 最终要记住什么？

> 向量库的选择是工程约束的结果；多租户检索最重要的细节，是每次查询都不能漏掉租户过滤。

## Day98 · Compose、本地 Linux 运维与可交付环境

说明在：[day98/README.md](../day98/README.md)

Day98 做的事情是：**把 PostgreSQL、Redis 和 Qdrant 固定成本地可复现的交付单元，并在启动前拒绝明显不安全的配置。**

### 1. 三个依赖的职责

```text
PostgreSQL → 会话真相源
Redis      → 缓存与限流
Qdrant     → 向量检索后端
```

`compose.yaml` 为三个服务配置数据卷和 healthcheck，端口默认只绑定到 `127.0.0.1`，避免把数据库端口直接暴露到公网。Linux 手册补充了拉取、启动、健康检查、备份、恢复和回滚步骤。

### 2. 启动前配置检查

```text
RuntimeSettings
  → DATABASE_URL 必须是 postgresql://
  → REDIS_URL 必须是 redis://
  → QDRANT_URL 必须是 HTTP(S)
  → production 禁止 change-me 示例密码
```

配置不符合要求时，`configuration_errors` 返回错误列表，让启动流程可以在真正连接外部服务前发现问题。它不会把开发默认值伪装成生产可部署配置。

### 3. Day98 的边界

Compose 是单机交付起点，不等于 Kubernetes、ACK 或高可用发布。生产镜像应锁定 digest，密钥应由 Secret 或密钥管理服务注入；还需要 TLS、反向代理、集中日志、告警、容量测试和故障演练。

### 4. Day98 最终要记住什么？

> “本地能启动”只是交付的第一层；依赖、健康检查、配置安全和恢复路径也要一起写清楚。

## Day99 · 开源模型接入：OpenAI 兼容 Provider 契约

说明在：[day99/README.md](../day99/README.md)

Day99 做的事情是：**让客服业务依赖统一的模型服务配置，而不是绑定云 API、Ollama 或 vLLM 的具体 SDK。**

### 1. 统一端点配置

```text
name + base_url + model + api_key_env
  → validate_provider
  → OpenAICompatibleProvider
  → base_url + /chat/completions
```

`base_url` 必须是完整 HTTP(S) 地址，并以 `/v1` 结束；`model` 不能为空；`api_key_env` 只能是环境变量名，不能把密钥值直接写进配置。生产环境还要求 HTTPS，或经过验证的内部 mTLS 代理。

### 2. 业务和厂商解耦

```text
客服工作流
  → base_url / model / 凭据引用
  → 云模型或自托管端点
```

业务代码只需要最小 OpenAI 兼容配置，就可以切换不同模型服务。这样解决的是调用入口的绑定问题，不代表不同模型在所有能力上完全一致。

### 3. Day99 的边界

OpenAI 兼容不保证 chat template、工具调用、JSON schema、embedding 或 token 统计语义相同。更换推理框架或模型后，仍要回放 Day53/Day89 的评测集，检查引用、拒答、工具和结构化输出。

### 4. Day99 最终要记住什么？

> 兼容 API 统一的是调用形状；真正能不能替换，还要由模型行为和回归数据证明。

## Day100 · vLLM 服务、GPU 配置与容器 Profile

说明在：[day100/README.md](../day100/README.md)

Day100 做的事情是：**把自托管推理服务的模型、端口、并行度、上下文和显存参数变成可校验配置，并让 GPU 服务只在可选 Compose profile 中启动。**

### 1. 结构化生成启动参数

```text
VllmServeSpec
  → 校验 model / port / 并行度 / 上下文 / 显存比例
  → vllm_command
  → tuple[str, ...] 参数列表
```

模型 ID 不能含空白，端口限制在 1–65535，张量并行度限制在 1–16，`max_model_len` 在 512–262144，显存利用率在 0.5–0.98。API key 只能引用环境变量名。

参数最终以列表返回，而不是拼成一条可注入的 shell 字符串；校验失败时直接抛出 `ValueError`。

### 2. GPU 服务是可选依赖

```text
compose.yaml + compose.vllm.yaml
  → --profile gpu
  → vLLM 容器
  → OpenAI 兼容端口
```

不启用 `gpu` profile 时，不要求本机必须有 GPU。启用时由环境变量提供模型、API key 和显存配置，容器端口仍默认绑定本机回环地址。

### 3. Day100 的边界

命令能启动不代表容量足够，也不代表模型支持工具调用、结构化输出或合适的中文 chat template。下一阶段要用基准数据验证延迟、吞吐和错误率，并重新跑 RAG 与客服回归集。

### 4. Day100 最终要记住什么？

> 自托管模型交付先把参数和启动边界写成代码，再用基准和业务回归判断它是否真的适合生产。

## Day91–Day100 总结：客服 Agent 的基础设施边界形成了什么？

```text
意图契约
  → 槽位状态与缺参追问
  → 显式工作流和人工转接
  → PostgreSQL RLS 会话真相源
  → 只读 SQL 与执行计划门禁
  → Redis 版本缓存与限流
  → 向量后端选型与 Qdrant 租户过滤
  → Compose 本地交付
  → OpenAI 兼容 Provider
  → vLLM GPU 服务配置
```

这一段把“客服 Agent 能对话”推进成“客服 Agent 有明确输入、状态、数据边界、检索边界和模型服务边界”。PostgreSQL、Redis、Qdrant 和 vLLM 都有真实接口或配置，但离生产 Kubernetes/ACK、高可用、企业身份系统和真实 GPU 容量压测仍有距离。
