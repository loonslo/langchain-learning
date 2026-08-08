# Day59 工作簿 · 人工升级闭环

## 0. 先确认本日变更闭环

| 文件 | 状态 | 它接到哪个旧文件/入口 | 如果不接会发生什么 |
|---|---|---|---|
| `src/customer_support/tickets.py` | 新增 | `SupportApplication.handle()` 的问答收尾 | 拒答只能返回一句提示，没有可追踪后续 |
| `tests/test_tickets.py` | 新增 | 验证无证据建单、有证据不重复建单 | 升级规则容易被误用 |
| `src/customer_support/application.py` | 修改旧文件 | 回答后调用 `escalate()` 并返回 `ticket_id` | 工单模块不会进入正式问答路径 |
| `src/customer_support/bootstrap.py` | 修改旧文件 | 创建并注入 `TicketStore` | 正式入口没有工单存储 |
| `tests/test_application.py` | 修改旧文件 | 验证拒答在正式入口能创建工单 | 只能证明独立函数，不能证明产品闭环 |

真实链路：`application.handle → assistant → escalate → TicketStore`

## 1. 从 Day58 继续

1. 前一天暴露的真实问题是什么？说“请转人工”不会自动留下用户、问题和原因，后续人员也没有可追踪编号。
2. 今天哪些旧文件被修改？为什么只新增模块还不够？修改 `application.py` 才能在正式回答之后判断是否升级；修改 `bootstrap.py` 才能注入工单存储。
3. 哪些继承文件虽然未改，却仍参与今天的调用链？`workflow.py`、`orders.py`、`tool_runner.py`、`assistant.py` 和 `conversation.py` 继续负责控制流、业务读取、重试、问答和会话。

## 2. 运行与证据

1. 哪条测试证明新能力已从正式入口可达？`test_refusal_creates_a_ticket_on_the_real_product_path`。
2. 哪条测试保护失败、安全或隔离边界？`test_missing_evidence_creates_open_ticket_but_answerable_question_does_not` 保护无证据建单、有证据不重复升级。
3. 运行 `materialize_day.py 59`，记录累计测试数量和结果：截至 Day59 累计 21 passed、15 条依赖弃用警告。
4. 暂时断开一个集成点，观察哪条测试失败，然后恢复：移除 `application.handle()` 对 `escalate()` 的调用会让正式入口测试失败；已恢复。

## 3. 今日结论

1. 今天仍不能证明什么？内存工单尚未幂等持久化，重复请求、进程重启和并发写入仍需要真实存储方案。
2. 用 60 秒说明：旧问题是人工升级没有落地；新增工单对象和创建规则；修改正式编排与组合入口；测试覆盖拒答建单和有证据不建单；边界是还没有持久化与幂等。
