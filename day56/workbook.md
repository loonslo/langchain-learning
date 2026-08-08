# Day56 工作簿 · LangGraph 显式控制流

## 0. 先确认本日变更闭环

| 文件 | 状态 | 它接到哪个旧文件/入口 | 如果不接会发生什么 |
|---|---|---|---|
| `src/customer_support/workflow.py` | 新增 | `SupportApplication` 通过正式入口调用 `WorkflowAssistant` | 新图不会进入产品链，应用仍走旧的混杂问答路径 |
| `tests/test_workflow.py` | 新增 | 验证空问题、无证据拒答和 `ask()` 适配契约 | 分支边界可能只停留在设计里 |
| `pyproject.toml` | 修改旧文件 | 加入 LangGraph 依赖和截至 Day56 的测试配置 | 运行环境无法还原今天的图控制流 |
| `src/customer_support/bootstrap.py` | 修改旧文件 | `build_application()` 注入 `WorkflowAssistant` | 新图不会被正式应用使用 |

真实链路：`app → bootstrap → SupportApplication → WorkflowAssistant/LangGraph → assistant`

## 1. 从 Day55 继续

1. 前一天暴露的真实问题是什么？校验、检索、拒答和生成开始互相嵌套，继续往一个函数里加分支会难以确认每条路径的出口。
2. 今天哪些旧文件被修改？为什么只新增模块还不够？修改 `bootstrap.py` 是为了让正式入口创建并使用图；只新增 `workflow.py` 只能得到孤立 Demo。
3. 哪些继承文件虽然未改，却仍参与今天的调用链？`application.py`、`assistant.py`、`conversation.py`、`knowledge.py` 和 `settings.py` 继续提供入口、问答、会话、检索和配置。

## 2. 运行与证据

1. 哪条测试证明新能力已从正式入口可达？`test_workflow_adapter_keeps_the_product_ask_contract` 证明图仍能通过 `ask()` 交给产品入口。
2. 哪条测试保护失败、安全或隔离边界？`test_graph_stops_invalid_and_refuses_without_evidence` 证明空问题不检索、无证据不生成。
3. 运行 `materialize_day.py 56`，记录累计测试数量和结果：截至 Day56 累计 17 passed。
4. 暂时断开一个集成点，观察哪条测试失败，然后恢复：移除 `bootstrap.py` 对 `WorkflowAssistant` 的注入会让正式入口无法获得显式控制流；已恢复。

## 3. 今日结论

1. 今天仍不能证明什么？用了 LangGraph 不等于自主 Agent；今天只是把固定校验、检索、拒答和生成路径画清楚并执行。
2. 用 60 秒说明：旧问题是分支混在问答里；新增图状态和条件边；修改组合入口接入正式链；测试覆盖非法输入和无证据；边界是没有证明系统具备自主规划能力。
