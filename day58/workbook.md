# Day58 工作簿 · 工具超时与有限重试

## 0. 先确认本日变更闭环

| 文件 | 状态 | 它接到哪个旧文件/入口 | 如果不接会发生什么 |
|---|---|---|---|
| `src/customer_support/tool_runner.py` | 新增 | `application.handle()` 的只读订单路径 | 失败分类和重试规则会散落在业务代码里 |
| `tests/test_tool_runner.py` | 新增 | 验证临时错误达到上限前可重试 | 重试次数可能无限增长 |
| `src/customer_support/application.py` | 修改旧文件 | 用 `call_read_only()` 包住订单读取 | 新的重试策略不会进入真实产品链 |
| `tests/test_application.py` | 修改旧文件 | 验证正式订单路径确实使用重试策略 | 只测工具函数，无法证明业务入口接通 |

真实链路：`application.handle → call_read_only → OrderRepository → 有限重试结果`

## 1. 从 Day57 继续

1. 前一天暴露的真实问题是什么？订单读取面对真实上游时会遇到暂时性失败，不能一次失败就把用户挡回去；但永久错误也不能被重复调用。
2. 今天哪些旧文件被修改？为什么只新增模块还不够？修改 `application.py` 才能把订单调用接入重试包装；只新增工具模块不会改变业务行为。
3. 哪些继承文件虽然未改，却仍参与今天的调用链？`orders.py` 提供真实订单读取，`conversation.py` 和 `assistant.py` 继续处理普通问答。

## 2. 运行与证据

1. 哪条测试证明新能力已从正式入口可达？`test_product_order_path_uses_the_read_only_retry_policy`。
2. 哪条测试保护失败、安全或隔离边界？`test_transient_error_retries_with_hard_limit` 证明临时错误最多两次，不会无限重试。
3. 运行 `materialize_day.py 58`，记录累计测试数量和结果：截至 Day58 累计 20 passed。
4. 暂时断开一个集成点，观察哪条测试失败，然后恢复：移除 `application.py` 对 `call_read_only()` 的调用会让产品路径测试失败；已恢复。

## 3. 今日结论

1. 今天仍不能证明什么？写操作不能直接套用读重试；业务异常还要先映射成明确的临时/永久错误，当前代码没有替你完成所有适配。
2. 用 60 秒说明：旧问题是上游暂时失败；新增错误分类和硬上限；修改订单入口接入包装；测试证明临时错误只重试一次；边界是只读策略不能泛化到写操作。
