# Day101–Day105 详细章节概括：用性能证据和企业协议完成跨 Agent 验收

这一组承接 Day100 的自托管 vLLM 配置，继续把模型服务放进可比较的性能门禁，再补上企业 HTTP MCP 鉴权、A2A Agent 协作协议和最终的客服 Agent → 订单 Agent 集成。重点从“服务能启动”转向“调用能授权、任务能追踪、协议能验收”。

## Day101 · 推理基准：量化、KV Cache 与容量决策

说明在：[day101/README.md](../day101/README.md)

Day101 做的事情是：**把量化、FlashAttention 和 KV Cache 从面试名词变成可复现的性能决策，并在指标超出预算时阻止发布。** 质量先过客服和 RAG 回归门槛，再比较速度、显存和成本。

### 1. 一组请求如何变成基准摘要？

```text
RequestSample
  → 过滤成功请求
  → p50 / p95 延迟
  → p95 TTFT
  → 输出 token/s
  → 全量错误率
  → BenchmarkSummary
```

没有样本或没有成功请求时不能发布。延迟和 TTFT 只对成功请求统计，错误率仍按全部请求计算；p95 使用 nearest-rank，两个样本时会保留较慢的那个，不把尾延迟平均掉。

### 2. SLO 门禁

```text
BenchmarkSummary + InferenceSlo
  → p95 总延迟超标？
  → p95 TTFT 超标？
  → 错误率超标？
  → release_errors
  → 通过 / 阻止发布
```

门禁只检查代码中定义的延迟、首 token 时间和错误率阈值。配套决策卡还要求记录输入长度、并发、GPU、服务版本、显存和成本，并在量化或更换推理框架后重跑质量回归。

### 3. 这些优化分别解决什么？

```text
量化       → 压缩模型权重
KV Cache   → 保存活跃序列已计算的注意力状态
FlashAttention → 更高效地计算注意力
```

它们不是同一个开关，也不能互相替代容量规划。长上下文或高并发导致 OOM 时，要同时检查上下文长度、并发和 KV Cache 预算。

### 4. Day101 的边界

本地基准只有在模型、提示长度、并发、硬件和服务版本一致时才可比较。单请求速度不能直接当成并发生产吞吐，也不能因为显存够就跳过质量评测。

### 5. Day101 最终要记住什么？

> 推理优化要靠同条件指标和业务质量一起做决定，不能只看一次请求的速度或显存占用。

## Day102 · MCP HTTP 鉴权、最小权限与写工具审批

说明在：[day102/README.md](../day102/README.md)

Day102 做的事情是：**把本地 stdio MCP 的凭据边界推进到企业 HTTP resource server，在协议边界检查 audience、scope 和高风险工具审批。** MCP Server 不负责伪造企业 OAuth 身份系统，但必须拒绝不适合当前资源的访问令牌。

### 1. 工具授权链路

```text
bearer token
  → TokenVerifier.verify
  → AccessClaims(subject, audience, scopes, tenant_id)
  → audience 校验
  → required_scope 校验
  → 高风险工具审批校验
  → 允许调用 / McpAuthorizationError
```

`McpToolPolicy` 声明工具名、所需 scope 和是否需要人工审批。令牌的 audience 不包含当前 MCP resource、缺少工具所需 scope，或写工具没有 `approved=True` 时，都会拒绝。

### 2. 最小权限不只看用户身份

```text
当前资源
  + token audience
  + 工具 scope
  + 用户/人工审批
  → 最终授权
```

服务端使用验证器提供的 claims，不能信任客户端自己传来的 `user_id`；也不能把收到的 access token 原样转发给不相关的下游工具。委托调用还应重新建立对应的权限上下文。

### 3. Day102 的边界

真实 OAuth issuer、JWKS key rotation 和企业 SSO 属于外部身份平台。本阶段实现的是 MCP resource-server 的授权策略，不是一个可替代企业 IdP 的身份系统。

### 4. Day102 最终要记住什么？

> 企业工具调用要在资源、权限和审批三处同时过关；“拿到了 token”不等于“可以调用任意工具”。

## Day103 · A2A Agent Card、任务生命周期与幂等

说明在：[day103/README.md](../day103/README.md)

Day103 做的事情是：**让独立 Agent 通过能力卡和任务协议协作，并让网络重试不会重复创建退款或订单任务。** A2A 不是把多个 LangGraph 节点简单放在同一个进程里。

### 1. 先发现能力，再提交任务

```text
Agent Card
  → 名称 / 地址 / 版本 / skills / 认证方式
  → messageId + message
  → InMemoryTaskStore.submit
  → AgentTask
```

`AgentCard` 公开 Agent 的能力、输入输出模式、是否支持流式和认证方案，但不放密钥。`AgentTask` 保存任务 ID、上下文 ID、消息 ID、状态和更新时间。

### 2. 任务状态不是随意改的

```text
submitted
  → working
  → input-required / completed / canceled / failed

submitted → rejected / auth-required
```

状态迁移由 `_TRANSITIONS` 白名单控制，终态 `completed`、`canceled`、`failed` 和 `rejected` 不能重新启动。任务需要输入时可以回到 `working`，授权失败则进入 `auth-required`。

### 3. `messageId` 提供幂等边界

```text
同一个 messageId 第一次提交 → 创建 task
同一个 messageId 再次提交   → 返回原 task
```

`InMemoryTaskStore` 用 `message_id → task_id` 做去重，所以客户端因网络超时重试时不会在内存里创建第二个任务。

### 4. Day103 的边界

当前仓储只适合离线学习。跨进程 A2A 服务需要把任务、去重键和审计事件写入持久化存储，并用认证身份决定租户和授权范围；内存幂等不能被直接当成生产保证。

### 5. Day103 最终要记住什么？

> Agent 协作需要能力声明、任务状态和幂等键三类契约，不能只交换一段自然语言。

## Day104 · A2A JSON-RPC、REST 与 SSE 边界

说明在：[day104/README.md](../day104/README.md)

Day104 做的事情是：**把 Day103 的任务模型暴露成可调用的 A2A HTTP 边界，并明确 JSON-RPC、REST 和 SSE 各自负责什么。**

### 1. JSON-RPC 方法

```text
message/send → 创建或幂等返回任务，并同步执行 handler
tasks/get   → 查询任务
tasks/cancel → 取消任务
```

方法名使用 `message/send`，不是旧版本的 `tasks/send`。`dispatch` 对 JSON-RPC 版本、参数形状、未知方法、任务不存在和非法状态分别返回错误码，避免把所有失败都伪装成成功结果。

### 2. REST 和发现入口

```text
GET  /.well-known/agent.json
POST /                 → JSON-RPC dispatcher
POST /v1/message:send  → 提交消息
GET  /v1/tasks/{id}    → 查询任务
POST /v1/message:stream → 返回 SSE
```

Agent Card 从 well-known 地址公开；REST 提交和查询使用任务模型；`sse` 把任务状态序列化成 `data: ...` 事件。当前工厂没有把每一个 JSON-RPC 方法都重复做成 REST 路由，取消能力通过 `tasks/cancel` 暴露。

### 3. 错误和流式边界

```text
Invalid Request / Invalid params / Method not found
Task not found / 非法状态迁移
  → JSON-RPC error
```

课程版 handler 会同步完成小任务，然后返回一个 SSE 事件。真实长任务应由队列和 worker 执行，状态写入持久库，并补上重连、超时、取消、回调推送和 trace。

### 4. Day104 最终要记住什么？

> 协议接入不只是加一个 HTTP 路由，还要把方法名、错误码、任务状态和流式事件格式固定下来。

## Day105 · 客服 Agent → 订单 Agent：企业协议集成验收

说明在：[day105/README.md](../day105/README.md)

Day105 做的事情是：**把客服 Agent 通过受控委托调用订单 Agent 的最小跨 Agent 场景跑通，并用离线验收覆盖关键边界。** 这里 MCP 用于 Agent 连接企业工具，A2A 用于独立 Agent 协作，二者职责不同。

### 1. 委托上下文不携带密钥

```text
tenant_id + subject + scopes + request_id
  → DelegationContext
  → metadata
  → A2A message/send
```

`DelegationContext` 只携带租户、主体、权限范围和请求编号，不包含数据库凭据或 bearer token。当前 `InProcessA2AClient` 是测试替身，真实版本应通过 Agent Card 声明的 endpoint 使用 HTTPS 调用远端 Agent。

### 2. 订单 Agent 的真实分支

```text
客服问题
  → 提取 order_id
  → 没有订单号？input-required
  → 没有 orders.read？auth-required
  → 调用 OrderReader.status(tenant_id, subject, order_id)
  → completed
```

订单号仍然来自确定格式的槽位抽取，不是凭空由 A2A 协议推断。订单 Agent 缺少订单号时返回“请提供订单号”；委托没有 `orders.read` scope 时拒绝；权限和参数齐全后，才通过已授权的订单读取器查询状态。

### 3. 客服侧如何接住结果？

```text
A2A error
  → 订单服务暂时不可用，转人工
input-required
  → 把缺参提示交给用户
auth-required
  → 告知当前账号无权查询
completed
  → 返回订单状态消息
```

`SupportOrderDelegator` 不把不同分支混成一个成功结果，而是根据任务状态分别处理。`acceptance.py` 还会离线验证意图槽位、JSON 契约、Qdrant 租户过滤和 A2A 订单状态，整个验收不依赖 Docker、GPU 或真实 LLM。

### 4. Day105 的边界

这是一套可讲、可测的企业 Agent 项目骨架，不应声称已经完成 Kubernetes/ACK、高可用发布、企业 IdP 对接、真实 GPU 容量压测或生产 A2A 联调。后续深度取决于目标岗位和真实部署环境。

### 5. Day105 最终要记住什么？

> 跨 Agent 集成的重点是把身份、租户、权限、任务状态和失败出口一起传递，而不是只把两个 Agent 的文本拼起来。

## Day101–Day105 总结：从可启动模型服务到跨 Agent 交付验收

```text
推理基准与 SLO 门禁
  → MCP audience / scope / 审批
  → A2A Agent Card
  → Task 状态与 messageId 幂等
  → JSON-RPC / REST / SSE 边界
  → 客服 Agent 委托订单 Agent
  → 离线集成验收
```

Day105 结束时，企业客服 Agent 已经有一条可解释、可测试的进阶主线：先用质量和性能证据判断模型服务，再在 MCP 边界保护企业工具，最后通过 A2A 任务协议调用独立订单 Agent。项目仍保留真实外部依赖边界：OAuth/企业 IdP、远端 A2A 服务、持久化任务仓储、生产 GPU 容量和高可用部署都需要在目标环境中继续完成。
