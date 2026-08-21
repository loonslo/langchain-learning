# Day81–Day90 详细章节概括：建立 AI 自动化测试专项的完整闭环

这一组是仓库里的可选 AI 自动化测试专项。它不再新增客服业务功能，而是围绕 Day78/Day79 的客服 Copilot 建立独立测试工程：风险、数据、契约、RAG、Judge、Agent、API、韧性、CI，最后把线上 bad case 回流成经过人工审核的回归用例。

## Day81 · 评测集与测试数据工程

说明在：[day81/README.md](../day81/README.md)

Day81 做的事情是：**把 Day80 的风险清单转成可版本化、可校验、可回放的结构化评测数据。**

### 1. 从 Risk 到 EvalCase

```text
RiskMatrix
  → 高风险业务场景
  → EvalCase
  → RAG / Judge / CI 共用
```

一条评测 case 至少要能描述问题、期望答案、标签、来源和版本，而不是只保存一句用户问题。

### 2. 数据工程能力

```text
schema 校验
版本标识
标签切片
JSON 持久化
坏数据失败
```

例如可以按 `rag`、`auth`、`streaming` 标签切出不同测试层，或者在版本升级后回放同一批 case。

### 3. Day81 的边界

数据结构合法不代表参考答案正确。标准答案仍需人工审查，后续 Judge 也要做校准。

### 4. Day81 最终要记住什么？

> 评测数据本身也是产品资产：要可校验、可版本化、可按标签切片、可回放。

## Day82 · Mock、契约与不变量测试

说明在：[day82/README.md](../day82/README.md)

Day82 做的事情是：**给 Day78 `/chat` 响应建立稳定契约，防止 Mock 全部通过但真实字段或业务规则已经变了。**

### 1. 契约测试什么？

```text
字段是否存在
字段类型是否正确
来源列表结构是否正确
拒答时是否有正确状态
升级时是否返回工单编号
```

### 2. 不变量测试什么？

```text
有工单编号 → 应该是升级结果
拒答结果   → 不应该伪造正常答案
引用来源   → 必须来自允许的来源结构
```

这些规则可以不依赖真实 LLM，直接用确定性输入验证。

### 3. Mock 和契约的分工

```text
Mock       → 替代昂贵/不稳定外部依赖
契约测试   → 保证接口形状
不变量测试 → 保证关键业务关系
```

契约通过不代表模型内容正确，它只是保证系统的边界没有被 Mock 掩盖。

### 4. Day82 最终要记住什么？

> 替身验证调用行为，契约和不变量验证边界；三者不能互相替代。

## Day83 · RAG 分层自动化测试

说明在：[day83/README.md](../day83/README.md)

Day83 做的事情是：**把 RAG 的召回、排序和引用拆开测，定位最终答案错误到底发生在哪一层。**

### 1. 计算 Recall@k 和 Precision@k

```text
Recall@k    → 期望来源有没有被召回
Precision@k → 召回结果里有多少是真相关
```

召回一个正确文档但混入十个无关文档，Recall 可能不错，Precision 就会暴露噪声。

### 2. 计算 MRR 和引用覆盖率

```text
MRR        → 第一条正确结果排得靠不靠前
引用覆盖率 → 答案需要的证据是否被引用
```

同样召回了正确文档，排在第 1 位和第 10 位，对生成模型的影响不同。

### 3. 这一层不调用真实 LLM

```text
EvalDataset
  → Retriever / ChatResponse 的来源列表
  → RetrievalCase
  → RAG metrics
```

先把检索层测稳定，避免每次评测都被生成随机性和 API 成本干扰。

### 4. Day83 最终要记住什么？

> RAG 不能只测最终答案；至少要分别测召回、排序、引用和生成。

## Day84 · 校准 LLM-as-Judge

说明在：[day84/README.md](../day84/README.md)

Day84 做的事情是：**用人工标签验证 Judge 的分数是否可信，并寻找合适的自动判定阈值。**

### 1. Judge 校准链路

```text
人工标签 + Judge score
  → 搜索 threshold
  → agreement
  → Cohen's kappa
  → 混淆矩阵
  → 判断是否采信自动分数
```

不是 Judge 给了 4.8 分就自动认为通过，而是先看它和人工判断的一致程度。

### 2. 混淆矩阵能看什么？

```text
人工通过 / Judge 通过 → 真正例
人工失败 / Judge 失败 → 真负例
人工失败 / Judge 通过 → 漏检
人工通过 / Judge 失败 → 误杀
```

漏检可能让坏版本进入 CI，误杀会让团队不信任门禁。

### 3. Day84 的边界

校准样本过少或分布单一时，kappa 可能不稳定；报告必须保存样本来源、人工版本和校准版本。

### 4. Day84 最终要记住什么？

> Judge 是测量工具，不是真值；上线自动评分前，必须有人工一致性证据。

## Day85 · 测试 Agent 行为轨迹

说明在：[day85/README.md](../day85/README.md)

Day85 做的事情是：**检查 Agent 最终回答之外的工具、参数、审批和步骤行为。**

### 1. 用 `TrajectoryPolicy` 审查轨迹

```text
Agent trace
  → 工具白名单检查
  → 工具参数检查
  → 写操作审批检查
  → 步骤预算检查
  → pass / fail
```

### 2. 为什么最终答案不够？

```text
答案：已查询订单
轨迹：实际上调用了别人的订单查询工具
```

或者：

```text
答案：已提交审批
轨迹：跳过审批直接执行写操作
```

所以 Agent 的行为轨迹本身就是产品输出。

### 3. Day85 最终要记住什么？

> 轨迹合法不等于答案正确，但没有轨迹测试，答案正确也可能掩盖越权和危险动作。

## Day86 · 测试 API、流式输出和端到端边界

说明在：[day86/README.md](../day86/README.md)

Day86 做的事情是：**站在 HTTP 和浏览器连接边界，验证 API 字段、SSE 事件顺序、token 合并以及前后端最终看到的结果。**

### 1. SSE 事件处理

```text
HTTP response
  → SSE parser
  → 检查 event_id / 顺序
  → 合并 token
  → ChatResponse contract
  → UI assertion
```

### 2. 为什么单元测试不够？

单元测试可能验证了 application 返回正确字典，但真实 HTTP 还可能出现：

```text
字段序列化变化
SSE 事件顺序错误
事件 ID 重复
代理截断流
前端合并 token 错误
```

### 3. Day86 的边界

离线 SSE 解析只能验证算法，不能代表真实浏览器、代理和上游服务稳定；真实 E2E 仍需要受控环境。

### 4. Day86 最终要记住什么？

> E2E 测试要验证用户实际收到的网络事件序列，而不仅是后端函数返回值。

## Day87 · 安全、韧性与性能测试

说明在：[day87/README.md](../day87/README.md)

Day87 做的事情是：**把输入边界、故障恢复和性能预算放到同一套自动化判定里。**

### 1. 输入边界

```text
过长问题 → 拒绝或截断
非法字段 → 校验失败
危险参数 → 不进入工具
```

输入验证要在模型调用前发生，不能让模型替应用做安全过滤。

### 2. 有限重试和退避

```text
临时失败
  → 预算内重试
  → 退避
  → 成功或明确失败
```

测试要验证不会无限重试，也不会对永久错误重复调用。

### 3. p95 SLO 判定

```text
延迟样本 + 错误样本
  → p95
  → error rate
  → SLO pass / fail
```

### 4. Day87 最终要记住什么？

> “接口能通”不等于“系统可靠”；安全输入、有限恢复和性能预算必须一起测。

## Day88 · CI 分层门禁和 flaky 防护

说明在：[day88/README.md](../day88/README.md)

Day88 做的事情是：**把各种测试层汇总成 CI 的单一发布判定，并识别偶发失败。**

### 1. 测试层分开统计

```text
unit
contract
rag_eval
security
performance / SLO
```

每一层都形成 `LayerResult`，记录通过、失败、缺失和是否为必需层。

### 2. 质量门必须失败关闭

```python
gate = evaluate_gate(results)
if not gate.passed:
    raise SystemExit(1)
```

必需层缺失、关键指标失败或安全层失败，都不能因为其他层通过而放行。

### 3. flaky 不能靠静默重跑掩盖

偶发失败需要被识别和记录。盲目重跑直到绿色，会让团队看不到真实不稳定性，也会把不可靠测试变成虚假的质量信号。

### 4. Day88 最终要记住什么？

> CI 门禁只负责按既定标准阻止回归；它不能替代风险分析、测试数据设计、人工校准和线上监控。

## Day89 · 建立线上质量反馈闭环

说明在：[day89/README.md](../day89/README.md)

Day89 做的事情是：**把用户点踩产生的 bad case 经过人工审核后，重新变成回归用例。**

### 1. 反馈闭环

```text
Day79 前端 / Day78 API feedback
  → BadCase
  → review_queue
  → human approve
  → regression.json
  → Day88 CI gate
```

### 2. 重复 case 不能污染队列

```python
queue.submit(BadCase("bad-1", ...))  # True
queue.submit(BadCase("bad-1", ...))  # False
```

同一个 `case_id` 只进入一次，避免一个线上问题因为用户重复点踩而在评测集中出现很多份。

### 3. 只有人工批准才能导出

```python
queue.approve("bad-1")
queue.export_regression_cases(path)
```

pending case 不会进入回归 JSON；导出后还要重新运行评测，确认修复真的改善指标。

### 4. Day89 最终要记住什么？

> 线上反馈可以进入测试闭环，但不能未经审核直接污染生产 Prompt 或评测集。

## Day90 · 当前仓库没有对应课程文件

截至当前仓库，Day80–Day89 全部存在，但还没有 `day90/` 目录或对应入口文件，因此这里不虚构 Day90 的课程内容。

## Day81–Day89 总结：AI 自动化测试专项形成了什么？

```text
风险建模
  → 评测数据
  → API 契约和不变量
  → RAG 分层指标
  → Judge 校准
  → Agent 轨迹
  → API / SSE / E2E
  → 安全、韧性、性能
  → CI 分层门禁
  → 线上反馈回归
```

Day89 结束时，专项形成了完整闭环：先按风险决定测什么，再用分层测试验证系统，最后把线上失败经过人工审核带回回归集。
