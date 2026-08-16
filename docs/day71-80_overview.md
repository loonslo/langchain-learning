# Day71–Day80 详细章节概括：从生产准备到最终验收，再进入 AI 测试专项

这一组的主线是：抽象向量存储以支持迁移，做容量和发布判定，建立反馈、降级、备份恢复和统一编排，最后准备面试证据、执行最终验收，并用 Day79 前端展示成果；Day80 开始进入独立的 AI 自动化测试专项。

## Day71 · 抽象 VectorStore，准备迁移到 pgvector

说明在：[day71/README.md](../day71/README.md)

Day71 做的事情是：**让业务代码依赖 VectorStore 契约，而不是直接依赖 Chroma，为共享数据库迁移做准备。**

### 1. 为什么不能让业务到处 import Chroma？

如果 `assistant.py`、同步模块和 API 都直接调用 Chroma，未来换 pgvector 时，所有业务模块都要改，测试也会一起失效。

### 2. 定义存储契约

```text
VectorStore.upsert(chunks)
VectorStore.delete_source(source_id)
VectorStore.search(query, k)
```

同步层只依赖这些操作：

```text
scan/plan
  → apply_plan
  → VectorStore.upsert / delete_source
```

当前可以有 Chroma 实现，未来可以有 Postgres/pgvector 实现。

### 3. 为什么同时准备 SQL schema？

`deployment/pgvector_schema.sql` 让未来的共享向量库有明确表结构、向量列和来源字段；迁移不是把数据库名字换一下，而是要提前定义存储契约和部署资产。

### 4. Day71 最终要记住什么？

> 先抽象业务依赖，再替换底层实现；迁移的第一步是稳定契约，不是立刻把所有代码改成新数据库 API。

## Day72 · 做容量评估和压测判定

说明在：[day72/README.md](../day72/README.md)

Day72 做的事情是：**解决“单次响应很快”不等于“并发容量足够”的问题。**

### 1. 看尾部延迟而不是只看平均值

```text
p50 → 一半请求至少这么快
p95 → 95% 请求至少这么快，关注慢请求尾部
error rate → 并发上来后有多少请求失败
```

客服服务的发布判断要结合 p95 和错误率，而不是只测一个请求得到 300ms 就宣布性能合格。

### 2. release readiness 调用链

```text
配置检查 + 压测样本
  → capacity report
  → release_readiness
  → 发布通过 / 失败
```

阈值应该可配置、可解释，并能在测试中验证通过和失败两条路径。

### 3. Day72 最终要记住什么？

> 容量不是一个“最快响应时间”，而是并发下 p95 延迟和错误率共同定义的可接受负载。

## Day73 · 建立用户反馈闭环

说明在：[day73/README.md](../day73/README.md)

Day73 做的事情是：**把用户点赞、点踩和 bad case 变成可以审查的改进队列。**

### 1. 反馈进入统一 API

```text
同一个 FastAPI
  ├─ /chat
  ├─ /knowledge/sync-plan
  └─ /feedback
          ↓
      FeedbackStore
```

反馈必须能关联到原请求、用户、来源和回答，后面才知道问题出在检索、生成还是业务流程。

### 2. 为什么负反馈不能自动改 Prompt？

```text
点踩
  → 进入 bad case 队列
  → 人工审查
  → 补充评测用例
  → 跑回归
  → 质量门通过后再发布
```

一个用户的误操作、恶意输入或错误评价都不能直接改变线上行为。

### 3. Day73 最终要记住什么？

> 用户反馈是数据飞轮的入口，不是自动修改生产系统的按钮。

## Day74 · 模型供应商故障时降级

说明在：[day74/README.md](../day74/README.md)

Day74 做的事情是：**主模型临时故障时切换到契约一致的备用模型，避免单一供应商故障直接中断服务。**

### 1. fallback 的调用链

```text
bootstrap
  → primary.invoke
  → 临时错误？fallback.invoke
  → 继续进入 workflow
```

### 2. 只对临时错误降级

```text
网络抖动 / 429 / 503 → 可以 fallback
参数错误 / 无权限    → 不应靠 fallback 掩盖
```

主模型和备用模型应保持相同的 `invoke` 契约，让上层 application 不需要知道当前用的是哪个供应商。

### 3. Day74 最终要记住什么？

> fallback 的目标是保持可用性，不是吞掉所有异常；备用模型也必须经过质量、延迟和契约测试。

## Day75 · 验证备份真的可以恢复

说明在：[day75/README.md](../day75/README.md)

Day75 做的事情是：**不仅生成备份文件，还实际验证恢复后数据库完整、会话可读、业务数据没有丢。**

### 1. 备份恢复链路

```text
正式 thread_db_path
  → SQLiteThreadStore.backup_to
  → 复制/恢复数据库
  → integrity_check
  → 读取线程和消息
  → 业务数据校验
```

### 2. 为什么文件存在还不够？

备份可能损坏、指向错误数据库、缺少关键表，或者恢复成功但租户/用户边界被破坏。因此要做数据库完整性检查和业务级断言。

### 3. Day75 最终要记住什么？

> 备份是手段，恢复演练和业务验证才是证据。

## Day76 · 把所有能力收进统一业务应用

说明在：[day76/README.md](../day76/README.md)

Day76 做的事情是：**把前面分散的安全、权限、缓存、工具、工单、反馈和同步能力收进一条真实请求链。**

### 1. 统一 runtime 到 application

```text
runtime
  → 认证 API
  → 统一 application
  → 安全检查
  → 缓存
  → RAG / 订单工具
  → 工单 / 反馈
  → trace 和结果
```

### 2. 为什么“文件存在”不等于“能力存在”？

如果 `security.py` 只是放在仓库里，但请求没有调用它，系统仍然没有注入防护。Day76 重点核对各模块是否真的接进 runtime 和 API。

### 3. Day76 最终要记住什么？

> 生产项目最终要证明的是请求经过了正确的边界，而不是仓库里堆了很多独立组件。

## Day77 · 把项目变成可验证的面试证据

说明在：[day77/README.md](../day77/README.md)

Day77 做的事情是：**把项目故事、简历表述和仓库中的真实文件、测试、运行结果绑定起来。**

### 1. 证据核验链

```text
项目陈述
  → runtime.verify_project_evidence
  → 检查真实模块、测试和证据文件
  → 输出可验证结果
```

### 2. 面试表达不能只说功能名

每个能力都要能回答：

```text
解决了什么问题？
为什么这样设计？
在哪里实现？
怎样验证？
边界和未完成部分是什么？
```

例如不能只说“支持多租户”，还要指出身份来源、读取边界和对应测试。

### 3. Day77 最终要记住什么？

> 面试只陈述仓库可验证的结果；没有测试或运行证据的能力不能包装成已经完成。

## Day78 · 执行毕业级最终验收

说明在：[day78/README.md](../day78/README.md)

Day78 做的事情是：**用统一 acceptance 流程验证整个客服 Copilot，而不是只演示 happy path。**

### 1. 验收覆盖哪些边界？

```text
RAG 答案与来源
无证据拒答
订单归属
人工工单
会话持久化
幂等写操作
安全注入
缓存隔离
质量门
备份恢复
```

### 2. 失败关闭

```text
任一关键安全或业务闭环失败
  → acceptance 失败
  → 不能只因为 happy path 成功而放行
```

### 3. Day78 最终要记住什么？

> “能跑一个成功案例”只是 Demo；毕业验收要覆盖失败、越权、恢复、退化和拒答路径。

## Day79 · 用前端工作台展示 Day78 API

说明在：[day79/README.md](../day79/README.md)

Day79 做的事情是：**不再新增一套后端，而是用 Vite 前端把 Day78 已经完成的能力展示出来。**

### 1. 浏览器到后端的链路

```text
浏览器页面
  → /api 代理
  → Day78 FastAPI
  → JWT 身份
  → 统一业务应用
  → RAG / 会话 / 订单 / 工单 / 反馈
```

### 2. 页面可以演示什么？

```text
JWT token 保存
多轮问答和新会话
知识来源展示
订单号进入只读工具
人工工单编号
点赞/点踩反馈
API 在线状态和错误提示
```

前端不会自己填写 `user_id`，身份仍然由 Day78 签名 token 决定。

### 3. Day79 最终要记住什么？

> Day79 的价值是把后端的安全、会话、来源、工具、工单和反馈能力变成用户可以直观看到的工作台。

## Day80 · AI 测试策略与风险建模

说明在：[day80/README.md](../day80/README.md)

Day80 做的事情是：**开始独立的 AI 自动化测试专项，用业务风险决定测试优先级，而不是按模块数量凭感觉排队。**

### 1. 用 `Risk` 描述风险

```python
risk = Risk(
    risk_id="RAG-01",
    area="retrieval",
    scenario="关键政策未召回",
    impact=5,
    likelihood=4,
    control="Recall@k",
)
```

风险分数是：

```python
score = impact * likelihood  # 20
```

代码还按分数分成 `critical`、`high`、`medium` 和 `low`。

### 2. `RiskMatrix` 做什么？

```python
matrix.add(risk)
matrix.prioritized()
matrix.uncovered_areas({"rag", "auth", "streaming"})
```

它负责高风险优先排序、拒绝重复风险编号，并报告还没有测试覆盖的区域。

### 3. Day80 的边界

风险矩阵只能回答“先测什么”，不能证明功能已经正确；Day81 会把高风险场景转成可执行的评测数据。

### 4. Day80 最终要记住什么？

> AI 测试计划应该从业务风险开始：风险评分 → 测试优先级 → 覆盖缺口，而不是看到哪个模块就先测哪个模块。

## Day71–Day80 总结：主线项目和测试专项如何衔接？

```text
存储抽象
  → 容量与发布判定
  → 反馈闭环
  → 模型降级
  → 备份恢复
  → 统一业务入口
  → 面试证据
  → 最终验收
  → 前端工作台
  → 风险驱动测试策略
```

Day80 结束时，主线客服项目完成生产闭环，同时开始用风险矩阵规划 Day81–Day89 的 AI 自动化测试专项。
