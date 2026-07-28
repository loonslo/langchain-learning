# AI 自动化测试可选补充包（Day79–88）

> 主线目标仍是 AI Agent / LLM 应用开发。本补充包只用于 backup 投递：AI 自动化测试工程师 / 大模型应用测试工程师 / AI 质量工程师。  
> 使用方式：完成 AI 应用开发主线后，根据目标 JD 选学相关单元，不要求 Day79–88 全部完成。

## 1. 岗位边界

AI 自动化测试不只是“测模型回答对不对”，而是测试整个 AI 应用：

1. **确定性外壳**：API、鉴权、数据处理、结构化输出、工具参数、状态持久化、异常处理。
2. **概率性行为**：回答正确性、相关性、忠实度、拒答、安全性和稳定性。
3. **RAG 链路**：文档解析、chunk、召回、rerank、引用和答案生成。
4. **Agent 链路**：工具选择、参数、调用顺序、任务完成、HITL 和副作用安全。
5. **工程质量**：延迟、成本、并发、超时、重试、降级、线上监控和 badcase 回流。

测试工程背景能降低转岗的迁移成本，但不能只会调用评测框架。岗位要求你能定位问题落在哪一层，并能读懂、调试和小幅修改被测系统。

## 2. AI 应用测试分层

| 层级 | 测什么 | 主要手段 | PR 是否阻断 |
|------|--------|----------|-------------|
| L0 静态与契约 | schema、prompt 变量、工具定义、权限规则 | lint、JSON Schema、确定性断言 | 是 |
| L1 组件 | loader、splitter、retriever、parser、tool | pytest、fake/mock、参数化 | 是 |
| L2 行为评估 | 正确性、相关性、忠实度、拒答 | 规则、语义相似度、LLM-as-judge | 分级阻断 |
| L3 链路与 E2E | RAG、Agent、API、SSE streaming | 集成测试、轨迹断言、真实小样本 | 是 |
| L4 非功能 | 性能、成本、安全、韧性 | 压测、故障注入、对抗测试 | 夜间或发布门禁 |
| L5 线上质量 | 失败率、p95、漂移、badcase | trace、采样评估、告警、回流 | 发布/运营决策 |

原则：确定性检查必须稳定阻断；昂贵或有波动的模型评估采用 baseline 对比、重复采样和分级门禁，不能把一次随机低分直接当成产品回归。

## 3. 选学优先级

- **第一优先级（建议补）**：Day79–84、Day87。直接复用现有评测、pytest、RAG、Agent 和 CI 基础。
- **第二优先级（按 JD）**：Day85。岗位强调 API 自动化、流式或多租户时再补。
- **第三优先级（按 JD）**：Day86、Day88。岗位强调安全、性能或线上质量运营时再补。

## 4. Day79–88 计划

### Day79｜AI 测试策略与风险建模

- 画出被测系统：输入 → 检索 → prompt → 模型 → tool → 输出 → 监控。
- 把需求转换成可测质量属性和风险：答错、乱答、越权、误调用、超时、成本失控。
- 建立测试分层、严重级别和放行规则。

**验收物**：`capstone/TEST_STRATEGY.md`，包含测试范围、风险矩阵、指标定义和门禁分级。

### Day80｜评估集与测试数据工程

- 构造黄金问答、边界、对抗、拒答、多跳、引用、权限和工具安全 case。
- 每条 case 保存 `id/type/question/reference/reference_context_ids/expected_tools/forbidden_tools/tags`。
- 划分 smoke / regression / challenge / production-badcase；做版本号、变更记录和数据泄漏检查。
- 人工标注优先，合成数据用于扩充，不能未经抽检直接当黄金集。

**验收物**：一份版本化 schema；不少于 50 条用例，各类型有明确分布和来源。

### Day81｜确定性自动化：mock、契约与不变量

- 用 fake/mock 隔离 LLM、embedding、retriever 和外部工具，测试失败路径而不消耗 token。
- 校验 JSON/Pydantic schema、引用格式、工具参数、流式事件顺序和错误码。
- 掌握三类断言：精确契约、集合/范围不变量、变形测试（输入改写后关键事实不应变化）。
- 避免用重试掩盖缺陷；区分产品波动、评估器波动和基础设施失败。

**验收物**：`tests/unit/` 与 `tests/contract/`，离线、无 API key、稳定通过。

### Day82｜RAG 自动化测试

- 检索层：recall@k、precision@k、MRR/nDCG，基于 reference chunk/document ID 计算。
- 生成层：答案正确性、相关性、faithfulness、拒答正确率。
- 引用层：citation correctness 与 citation completeness；不要把“答案出现来源二字”当引用正确。
- 对 chunk size、overlap、embedding、top-k、rerank 做同集 A/B，并输出失败归因。

**验收物**：一条能区分“没召回、排错序、召回后生成错、引用错”的 RAG 评测报告。

### Day83｜LLM-as-judge 的校准与可信度

- 为每个指标写单一维度 rubric、正反例和结构化评分输出。
- 建人工标注集，计算 judge 与人的一致性：分类结果用 Cohen's kappa；连续/等级分同时看相关性和分档一致率。
- 测 position bias、verbosity bias、self-preference；必要时交换顺序、多次评审或多 judge 仲裁。
- 版本化 judge 模型、prompt 和阈值，judge 变化必须重新校准。

**验收物**：judge 校准报告，记录样本、分歧 case、kappa、阈值选择和适用边界。

### Day84｜Agent 自动化测试

- 结果指标：任务成功率、最终答案/副作用是否正确。
- 过程指标：工具选择、参数、顺序、禁止工具、最大步数、循环和成本。
- 测 timeout、工具报错、重复调用、幂等、checkpoint 恢复和 HITL 中断/继续。
- 区分“允许多条正确轨迹”和“必须满足的关键约束”，避免把唯一理想轨迹写死。

**验收物**：真实 Agent 运行轨迹进入评测器，不使用手写 demo trajectory 冒充实测。

### Day85｜AI API、流式与端到端测试

- 覆盖同步/异步接口、SSE streaming、断线重连、取消、超时和错误映射。
- 校验首 token 延迟、完整响应延迟、事件顺序、终止事件和半包/空包。
- 覆盖鉴权、多租户、会话隔离、并发会话和数据增量更新后的可检索性。

**验收物**：FastAPI E2E 自动化套件，包含流式、鉴权、跨租户隔离和异常 case。

### Day86｜安全、韧性与性能自动化

- 安全：prompt injection、越狱、PII、密钥泄露、文档越权、工具参数注入。
- 韧性：模型 429/5xx/超时、向量库不可用、工具异常、fallback 和熔断。
- 性能：并发、p50/p95/p99、首 token 延迟、吞吐、token 与单请求成本。
- 测试环境中的高风险工具必须 fake；不能让自动化测试产生真实邮件、删除或支付副作用。

**验收物**：安全与故障注入用例集、Locust 报告、SLO 门槛和恢复行为报告。

### Day87｜CI 分层门禁与防 flaky

- PR 快门禁：离线单元/契约测试 + 小型固定 smoke eval，控制在可接受时长和成本。
- Nightly 全量：完整回归集、多个模型样本、LLM judge、安全和性能测试。
- Release 门禁：candidate 对 baseline 的绝对阈值 + 相对跌幅；关键安全 case 一票否决。
- 分离产品失败、评估器失败、外部 API/网络失败；保存逐 case 结果、版本和 trace artifact。

**验收物**：故意改坏 prompt、工具路由和权限规则，CI 能分别给出可解释的红灯原因。

### Day88｜线上质量闭环与可选整合验收

- 线上采集 p95、错误率、token、成本、拒答率、工具失败率和人工反馈。
- 对生产 trace 分层采样，脱敏后人工/自动评估；聚类 badcase 并回流到 regression set。
- 完成一次“线上坏例 → 归因 → 修复 → 离线回归 → 灰度验证”的闭环。
- 把测试策略、数据集、报告、CI 结果和闭环复盘组织成作品集证据。

**验收物**：capstone 的统一 AI 质量流水线和一份可在面试中演示的改进报告。

## 5. 选择 AI 自动化测试方向时的 Capstone 增强项

当前 `capstone/evaluation.py`、`ci_gate.py`、`test_regression.py` 已形成最小闭环。若投递 AI 自动化测试岗位，可从以下增强项按 JD 选择，不影响 AI 应用开发主线验收：

1. 把 `evals/eval_cases.json` 的完整用例 schema 合并为 capstone 的单一数据源，消除 6 条简化用例与 52 条平台用例的割裂。
2. 将检索、生成、引用、Agent 轨迹拆成独立指标；`faithfulness` 不与“幻觉率”简单画等号。
3. 将真实 Agent trace 接入轨迹评测；demo trace 只用于单元测试。
4. 将 CI 拆成 PR smoke、nightly full eval、release gate，外部模型或 embedding 不可用时明确标记基础设施失败。
5. 保存 baseline/candidate、模型、prompt、数据集、judge、代码 commit、延迟和成本版本信息。
6. 建立线上 badcase 回流入口，并展示至少一次真实改进闭环。

## 6. Backup 岗位求职表达

推荐的一句话：

> 我搭过一套 AI 应用自动化质量流水线，把 RAG 召回、回答忠实度、Agent 工具轨迹、接口可靠性和安全 case 变成可回归、可追踪、能进入 CI 门禁的质量信号。

简历中的数字必须来自可复现报告，例如：

- 评估集多少条、覆盖哪些风险类型；
- recall@k、faithfulness、任务成功率的 baseline 与 candidate；
- 自动化运行时间、成本、flaky rate；
- 发现过什么回归，怎样定位并修复；
- 修复后提升多少，是否破坏其他指标。

避免使用“市面极稀缺”“面试官一听就知道”等无法验证的表述。作品证据比岗位口号更有说服力。
