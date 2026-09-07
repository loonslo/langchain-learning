# Step4 流程图与 Step2 节点变更

流程总览图：`step4-full-overview.png`

对比基线：`day31_40/step02_planning_observability.py`

当前版本：`day31_40/step04_evidence_generation.py`

## 当前流程

`START → intake → route → after_route`

- `in_scope=False`：`out_of_scope → END`
- `requires_approval=True`：`restricted_action → END`
- `missing_information` 非空：`clarify → END`
- `sources` 为空：`generate → END`
- `sources` 有值：`plan → supervisor → dispatch → specialist` 循环
- 没有待执行任务，或 `supervisor_steps > 10`：`compose_context → generate → END`

## 节点变更

| 节点 | Step2 | Step4 |
| --- | --- | --- |
| `intake` | 空白规范化、空问题校验 | 沿用 |
| `route` | 保存 `model.route()` 结果 | 只允许 `web/sql`；拦截来源写入 `errors` 和 `trace` |
| `after_route` | 按范围、审批、缺信息、来源选出口 | 判断顺序沿用；输入变成白名单过滤后的 `sources` |
| `clarify` | 缺信息后结束 | 出口沿用，提示语改为真实取证语境 |
| `out_of_scope` | 越界后结束 | 出口沿用，范围改为公开资料与已录入数据 |
| `restricted_action` | 受限动作后结束 | 出口沿用，明确只能查询，不能交易 |
| `plan` | 直接采用模型任务列表 | 过滤来源；空计划按来源兜底；重排 `parallel_group` |
| `supervisor` | 统计 pending 并记录 trace | 增加 `supervisor_steps`、耗时和预算提示 |
| `dispatch` | pending → `specialist`，否则汇聚 | 增加 `supervisor_steps > 10` 的退出条件 |
| `specialist` | `llm.invoke()` 生成说明性 `step02://` 证据 | `adapters[item.source].collect()` 做真实 Web/SQLite 取证；异常写 `errors` |
| `compose_context` | 只拼接编号和内容 | 加入 source、标题、reference、warning |
| `generate` | 消费 question/context 生成答案 | 输入基本沿用，新增生成耗时和长度 trace |

## 节点外变化

- `GraphState` 新增 `errors`、`supervisor_steps`，并统一 `trace` 类型。
- `ModelGateway` 从 `llm` 属性改为增加 `generate_sql()`，供 `SafeSqlAdapter` 使用。
- `build_graph()` 初始化 SQLite，并接入 `TavilySearchAdapter`、`SafeSqlAdapter` 和 `ResilientAdapter`。
- Step4 仍按顺序执行；真正的同组并行放在 Step5。
