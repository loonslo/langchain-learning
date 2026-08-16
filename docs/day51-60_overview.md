# Day51–Day60 详细章节概括：连续开发一个企业客服与工单 Copilot

从 Day51 开始，不再是互相孤立的小实验，而是沿着同一个客服产品不断加能力。主线是：先做可用客服 RAG，再补多文档、评测、混合检索、连续追问、工作流、订单工具、重试、工单和持久化会话。

## Day51 · 做出可自由提问的客服 RAG 最小产品

说明在：[day51/README.md](../day51/README.md)

Day51 做的事情是：**建立客服 Copilot 的第一条真实主链，让用户可以自由提问，并且只有在检索到证据时才让模型回答。**

### 1. 第一个可运行的产品结构

```text
settings.py   → 知识文件和模型配置
knowledge.py  → Markdown → chunks → Retriever
bootstrap.py  → 组装 embedding、Retriever、LLM
assistant.py  → 检索、拒答、回答、来源
app.py        → 交互式输入和展示
```

这一天不是再写一个独立 RAG demo，而是把入口、配置、依赖组装、业务逻辑分开。

### 2. 一次问答的真实调用链

```text
用户输入
  → app.py
  → bootstrap 创建真实依赖
  → CustomerSupportAssistant.ask
  → 检索证据
  → 无证据：直接拒答
  → 有证据：调用模型生成
  → 展示答案和来源
```

关键点是无证据时在模型调用前拒答，避免模型利用自己的通用知识编造客服政策。

### 3. Day51 的边界

它暂时只读取一份 FAQ，尚未支持多文档、连续追问、订单工具和持久化会话；这些能力会在后面逐步加入。

### 4. Day51 最终要记住什么？

> 客服 RAG 的最小产品不是“模型回答”，而是“证据检索 → 有证据才生成 → 返回真实来源”。

## Day52 · 把单个 FAQ 扩展成多文档知识库

说明在：[day52/README.md](../day52/README.md)

Day52 做的事情是：**把 Day51 的单文件知识库改成目录级摄取，让退款、配送等独立政策真正进入同一条问答链。**

### 1. 增加独立的 ingestion 层

```text
data/knowledge/*.md
  → ingestion.ingest_directory
  → 全部 chunks
  → knowledge.build_retriever
  → Chroma
```

`ingestion.py` 负责遍历文件、读取和切块，`knowledge.py` 负责构建检索器，二者不互相导入。

### 2. 每个 chunk 都要有稳定身份

```text
source     → 来源文件
source_id  → 稳定来源标识
chunk_id   → 稳定切块标识
```

相同资料重复摄取应该产生相同 `chunk_id`，后面才能做增量更新、去重和删除。

### 3. 用户入口为什么不用改？

Day51 的 `assistant.py` 只依赖 Retriever，并不关心 Retriever 背后是一份文档还是十份文档。因此 Day52 只替换摄取和建库内部，用户仍然直接运行 `customer_support.app`。

### 4. Day52 最终要记住什么？

> 多文档知识库的关键是“目录摄取 + 稳定来源标识 + 业务入口不感知底层变化”。

## Day53 · 用正式产品链执行离线评测

说明在：[day53/README.md](../day53/README.md)

Day53 做的事情是：**把固定评测题接到正式客服产品入口上，证明评测测的就是用户实际使用的链路。**

### 1. 评测数据包含什么？

```json
{
  "question": "如何申请退款？",
  "answer_keywords": ["退款"],
  "expected_sources": ["refund.md"],
  "should_refuse": false
}
```

它同时检查答案内容和引用来源，资料外问题还要检查是否正确拒答。

### 2. 评测不能复制业务逻辑

```text
eval_cases.json
  → evaluation.py
  → 正式 CustomerSupportAssistant.ask()
  → 多文档检索 + LLM
  → answer_ok / citation_ok
  → 报告和退出码
```

如果评测程序自己又写一套检索和 Prompt，那么测试通过不能说明正式产品通过。

### 3. 非零退出码有什么用？

```python
if any_case_failed:
    raise SystemExit(1)
```

开发者可以在本地看到失败，后续 CI 也可以根据退出码阻止发布。

### 4. Day53 最终要记住什么？

> 评测入口可以独立于用户入口，但必须复用同一个业务 `ask()`，否则测的是假系统。

## Day54 · 把混合检索接进产品主链

说明在：[day54/README.md](../day54/README.md)

Day54 做的事情是：**不仅写出 RRF 算法，而是让语义检索、关键词检索和融合排序真正进入用户问答和评测路径。**

### 1. 两路检索同时工作

```text
用户问题
  ├─ Chroma 语义检索
  └─ BM25 关键词检索
          ↓
        RRF 排名、去重
          ↓
  CustomerSupportAssistant
```

语义检索处理表达相近的问题，关键词检索处理“退款 7 天”“订单号”等精确业务词。

### 2. RRF 做什么？

```text
同一文档在多路结果中都靠前
  → 获得更高融合分
  → 多次出现的文档去重
  → 共同命中的证据优先交给模型
```

### 3. 为什么只新增 `retrieval.py` 不够？

如果 `knowledge.build_retriever()` 仍返回旧 Chroma retriever，那么混合检索就没有进入正式主链。Day54 特别强调要同时检查 `knowledge.py`、`bootstrap.py`、`assistant.py` 和评测入口。

### 4. Day54 最终要记住什么？

> 检索组件写出来不等于产品使用了它；必须沿真实调用链确认新能力从入口一直走到结果。

## Day55 · 支持连续追问和会话隔离

说明在：[day55/README.md](../day55/README.md)

Day55 做的事情是：**解决用户问“那发票呢”时，问题本身缺少上下文，单独检索无法理解指代的问题。**

### 1. 增加统一业务编排层

```text
app
  → bootstrap.build_application
  → SupportApplication
  → History / follow-up rewrite
  → assistant
```

`application.py` 负责统一入口，`conversation.py` 负责会话历史和追问改写，底层 `assistant.py` 继续负责检索、拒答、生成和来源。

### 2. 连续追问的大致流程

```text
“我想退款”
  → 记录历史
“那发票呢？”
  → 结合同一 session 的历史改写成独立问题
  → 送入检索器
```

不是每个问题都要带上全部历史，也不是把所有用户的历史混在一起。

### 3. 为什么要限制历史长度？

历史越长，token、延迟和噪声越高。第一版实现只做有限窗口和 session 隔离，后续更复杂的摘要和持久化会继续演进。

### 4. Day55 最终要记住什么？

> 连续追问的关键是“同一 session 的上下文改写 + 历史长度边界”，不是无限制地把聊天记录塞给模型。

## Day56 · 用 LangGraph 表达客服工作流

说明在：[day56/README.md](../day56/README.md)

Day56 做的事情是：**把校验、追问、检索、拒答和生成等分支写成显式状态图，同时保持原来的业务 `ask()` 契约不变。**

### 1. 为什么从普通函数进入 workflow？

当流程只有“检索然后生成”时，普通函数足够；但客服链开始出现：

```text
输入校验
  → 是否需要追问改写
  → 是否找到证据
  → 拒答 / 生成
```

分支越来越多时，显式图比一个超长函数更容易测试和定位。

### 2. 真实调用链

```text
app
  → bootstrap
  → SupportApplication
  → WorkflowAssistant / LangGraph
  → assistant
```

`WorkflowAssistant` 负责把图包装成原来调用方认识的 `ask()`，所以底层换成图后，用户入口和评测入口不用重写。

### 3. Day56 的边界

这里使用 LangGraph 主要是显式控制业务分支，并不等于已经做了一个自主 Agent；模型仍然只在规定节点中回答。

### 4. Day56 最终要记住什么？

> 只有出现状态和分支才引入图；引入图的目标是可控流程，不是为了给项目贴“Agent”标签。

## Day57 · 增加受控订单查询工具

说明在：[day57/README.md](../day57/README.md)

Day57 做的事情是：**让客服除了查知识库，还能查询用户自己的订单状态，并把资源归属检查放在数据访问边界。**

### 1. 订单工具处理的不是普通 FAQ

```text
订单号问题
  → application.handle
  → OrderRepository.get_for_user
  → 校验订单是否属于认证用户
  → 返回订单状态
```

RAG 适合退款政策、配送规则等文档；订单状态属于结构化、用户私有数据，应走受控工具。

### 2. 归属校验必须在仓库边界

```python
order = repository.get_for_user(order_id, user_id)
```

不能只在 Prompt 里告诉模型“不要看别人的订单”，也不能相信请求正文中的 `user_id`。业务层必须验证资源归属。

### 3. 错误要区分

```text
订单不存在 → OrderNotFound
订单不属于当前用户 → ForbiddenOrder
```

不同错误对应不同响应、日志和安全策略。

### 4. Day57 最终要记住什么？

> 工具读取业务数据前必须验证资源归属；模型知道订单号不代表它有权查看订单。

## Day58 · 给订单工具加超时和有限重试

说明在：[day58/README.md](../day58/README.md)

Day58 做的事情是：**把订单查询从“能查”升级成“上游临时失败时不会立刻崩，也不会无限重试”。**

### 1. 分类工具错误

```text
TransientToolError → 503、网络抖动、临时超时，可有限重试
PermanentToolError → 参数错误、无权限、资源不存在，不应重试
```

### 2. 受控调用入口

```python
result = call_read_only(
    repository.get_for_user,
    order_id,
    user_id,
    max_attempts=3,
)
```

工具运行器统一处理重试次数、退避和最终错误，让 application 不需要自己复制一套循环。

### 3. 为什么特别强调只读？

读操作重试一般不会制造新业务对象；写操作重试可能重复创建工单、重复扣款或重复发邮件。写操作需要先有幂等设计。

### 4. Day58 最终要记住什么？

> 重试策略和操作类型绑定：临时、只读、可恢复的失败才适合有限重试。

## Day59 · 证据不足时创建人工工单

说明在：[day59/README.md](../day59/README.md)

Day59 做的事情是：**把“请联系人工”变成真正可追踪的业务闭环。**

### 1. 无证据时不只是返回拒答

```text
检索不到可信证据
  → 不调用模型编造
  → 创建 open ticket
  → 返回“已转人工”和工单编号
```

有证据的问题则继续正常回答，不应该所有问题都无条件创建工单。

### 2. Ticket 是业务状态，不是一行提示

```text
Ticket
  → ticket_id
  → question / reason
  → status = open
  → created_at
```

这样人工团队才能查询、处理和关闭工单，用户也能用编号追踪。

### 3. Day59 最终要记住什么？

> 拒答是模型行为，升级是业务动作。没有工单对象、状态和编号，就没有真正的人工闭环。

## Day60 · 把会话历史持久化到 SQLite

说明在：[day60/README.md](../day60/README.md)

Day60 做的事情是：**解决 Day55 的内存会话重启即丢失问题，让客服历史可以在重启后恢复。**

### 1. 使用 SQLite thread store

```python
store = SQLiteThreadStore(db_path)
store.append(tenant_id, user_id, thread_id, message)
messages = store.load(tenant_id, user_id, thread_id)
```

`conversation.py` 的 `PersistentHistory` 通过这个存储实现追加和读取，应用层继续使用历史接口。

### 2. 读取边界由三部分组成

```text
tenant_id + user_id + thread_id
```

只用 `thread_id` 不够安全：攻击者可能猜到别人的线程 ID；只用 user 也无法区分同一用户的多个会话。

### 3. 这一天验证什么？

测试会验证：消息能持久化、重新创建 History 对象后仍能加载、不同租户/用户/线程之间互不读取。

### 4. Day60 最终要记住什么？

> 会话持久化不仅是“把消息写入数据库”，还必须设计租户、用户、线程三层读取边界。

## Day51–Day60 总结：客服产品从 Demo 变成了什么？

```text
单文档客服 RAG
  → 多文档摄取
  → 正式离线评测
  → 混合检索
  → 连续追问
  → 显式工作流
  → 订单工具与权限
  → 有限重试
  → 人工工单
  → SQLite 会话
```

Day60 结束时，这已经不再是“问答脚本”，而是一条有知识库、评测、会话、业务工具、工单和持久化的客服应用主链。
