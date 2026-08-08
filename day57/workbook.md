# Day57 工作簿 · 受控订单查询工具

## 0. 先确认本日变更闭环

| 文件 | 状态 | 它接到哪个旧文件/入口 | 如果不接会发生什么 |
|---|---|---|---|
| `src/customer_support/orders.py` | 新增 | `SupportApplication.handle()` 的订单分支 | 没有可复用的归属校验，业务数据容易被直接暴露 |
| `tests/test_orders.py` | 新增 | 直接验证订单存在且归属匹配 | 越权场景没有独立保护 |
| `src/customer_support/application.py` | 修改旧文件 | 在正式入口增加订单分支 | 新订单模块不会被用户请求调用 |
| `src/customer_support/bootstrap.py` | 修改旧文件 | 创建并注入订单仓库 | 生产组合入口拿不到订单数据源 |
| `tests/test_application.py` | 修改旧文件 | 验证订单能力从产品入口可达 | 单测通过也不能证明正式入口接通 |

真实链路：`app → application.handle → 订单归属查询或 RAG 问答`

## 1. 从 Day56 继续

1. 前一天暴露的真实问题是什么？FAQ 能回答固定知识，却不知道实时订单；而订单还是用户自己的业务数据，不能按普通检索结果直接返回。
2. 今天哪些旧文件被修改？为什么只新增模块还不够？修改 `application.py` 才能把订单请求分流到业务仓库，修改 `bootstrap.py` 才能把仓库注入正式入口。
3. 哪些继承文件虽然未改，却仍参与今天的调用链？`workflow.py`、`assistant.py`、`conversation.py`、`knowledge.py` 和 `settings.py` 继续处理普通问答和运行配置。

## 2. 运行与证据

1. 哪条测试证明新能力已从正式入口可达？`test_order_query_is_reachable_from_the_product_application`。
2. 哪条测试保护失败、安全或隔离边界？`test_order_query_enforces_ownership` 保护用户不能读取他人的订单。
3. 运行 `materialize_day.py 57`，记录累计测试数量和结果：截至 Day57 累计 18 passed。
4. 暂时断开一个集成点，观察哪条测试失败，然后恢复：移除 `application.handle()` 的订单分支会让正式入口测试失败；已恢复。

## 3. 今日结论

1. 今天仍不能证明什么？当前只有只读内存订单仓库，不能代表真实数据库、权限系统和并发场景。
2. 用 60 秒说明：旧问题是 FAQ 不含实时订单；新增按订单号和用户身份查询；修改正式编排和组合入口；测试覆盖可达性与越权；边界是数据源仍是内存实现。
