# Day62 工作簿 · 写操作幂等

## 0. 先确认本日变更闭环

| 文件 | 状态 | 它接到哪个旧文件/入口 | 如果不接会发生什么 |
|---|---|---|---|
| `src/customer_support/idempotency.py` | 新增 | 待填写 | 待填写 |
| `tests/test_idempotency.py` | 新增 | 待填写 | 待填写 |
| `src/customer_support/api.py` | 修改旧文件 | 待填写 | 待填写 |
| `src/customer_support/application.py` | 修改旧文件 | 待填写 | 待填写 |
| `src/customer_support/bootstrap.py` | 修改旧文件 | 待填写 | 待填写 |
| `tests/test_application.py` | 修改旧文件 | 待填写 | 待填写 |

真实链路：`Idempotency-Key → API → application → IdempotencyStore → TicketStore`

## 1. 从 Day61 继续

1. 前一天暴露的真实问题是什么？客户端重试可能创建重复工单（请用自己的话重写）
2. 今天哪些旧文件被修改？为什么只新增模块还不够？待填写。
3. 哪些继承文件虽然未改，却仍参与今天的调用链？待填写。

## 2. 运行与证据

1. 哪条测试证明新能力已从正式入口可达？待填写。
2. 哪条测试保护失败、安全或隔离边界？待填写。
3. 运行 `materialize_day.py 62`，记录累计测试数量和结果：待填写。
4. 暂时断开一个集成点，观察哪条测试失败，然后恢复：待填写。

## 3. 今日结论

1. 今天仍不能证明什么？内存实现尚未处理多实例并发（补充你的判断）
2. 用 60 秒说明：旧问题 → 新增能力 → 修改旧文件 → 调用链 → 测试证据 → 边界。
