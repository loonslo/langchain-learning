# Day62 · 写操作幂等

> 今天解决：客户端重试可能创建重复工单。
>
> 第一性原则：同一幂等键和请求只能执行一次。

## 1. 与 Day61 的文件衔接

先还原并跑通 Day61，再开始今天。不要只看新增文件：先确认今天修改了哪些旧文件，再沿“关键继承文件”检查新能力是否真的进入已有产品链。

### 今天新增、修改或删除

| 项目相对路径 | 状态 | 为什么今天要看 |
|---|---|---|
| `src/customer_support/idempotency.py` | 新增 | 写操作去重 |
| `tests/test_idempotency.py` | 新增 | 验证今天新增能力的正向和失败路径 |
| `src/customer_support/api.py` | 修改旧文件（上一版 Day61） | HTTP 契约 |
| `src/customer_support/application.py` | 修改旧文件（上一版 Day59） | 统一业务编排 |
| `src/customer_support/bootstrap.py` | 修改旧文件（上一版 Day60） | 创建真实依赖并接入正式主链 |
| `tests/test_application.py` | 修改旧文件（上一版 Day60） | 验证今天新增能力的正向和失败路径 |

### 关键继承文件

| 项目相对路径 | 状态 | 在今天链路中的作用 |
|---|---|---|
| `src/customer_support/assistant.py` | 继承 Day51，今天仍被变更代码调用 | 检索、拒答、生成与来源返回 |
| `src/customer_support/conversation.py` | 继承 Day60，今天仍被变更代码调用 | 会话历史与追问改写 |
| `src/customer_support/knowledge.py` | 继承 Day54，今天仍被变更代码调用 | 摄取结果与检索器的装配点 |
| `src/customer_support/orders.py` | 继承 Day57，今天仍被变更代码调用 | 订单归属查询 |
| `src/customer_support/settings.py` | 继承 Day60，今天仍被变更代码调用 | 截至今天的运行路径与环境配置 |
| `src/customer_support/thread_store.py` | 继承 Day60，今天仍被变更代码调用 | SQLite 会话 |
| `src/customer_support/tickets.py` | 继承 Day59，今天仍被变更代码调用 | 人工工单 |
| `src/customer_support/tool_runner.py` | 继承 Day58，今天仍被变更代码调用 | 工具错误分类与重试 |
| `src/customer_support/workflow.py` | 继承 Day56，今天仍被变更代码调用 | LangGraph 状态和分支 |

运行 `python tools/day_change_report.py 62` 可查看全部“继承未改”文件。

## 2. 今天结束后的真实调用链

```text
Idempotency-Key → API → application → IdempotencyStore → TicketStore
```

验收时必须能指出：新增能力从哪里被调用、结果交给谁、失败会在哪一层被拦住。

## 3. Day62 结束后的完整项目结构

```text
.env.example  # 继承 Day51
data/eval_cases.json  # 继承 Day53
data/knowledge/customer_faq.md  # 继承 Day51
data/knowledge/refund.md  # 继承 Day52
data/knowledge/shipping.md  # 继承 Day52
pyproject.toml  # 继承 Day61
src/customer_support/__init__.py  # 继承 Day51
src/customer_support/api.py  # 本日变更
src/customer_support/app.py  # 继承 Day55
src/customer_support/application.py  # 本日变更
src/customer_support/assistant.py  # 继承 Day51
src/customer_support/bootstrap.py  # 本日变更
src/customer_support/conversation.py  # 继承 Day60
src/customer_support/evaluation.py  # 继承 Day53
src/customer_support/idempotency.py  # 本日变更
src/customer_support/ingestion.py  # 继承 Day52
src/customer_support/knowledge.py  # 继承 Day54
src/customer_support/orders.py  # 继承 Day57
src/customer_support/retrieval.py  # 继承 Day54
src/customer_support/runtime.py  # 继承 Day61
src/customer_support/settings.py  # 继承 Day60
src/customer_support/thread_store.py  # 继承 Day60
src/customer_support/tickets.py  # 继承 Day59
src/customer_support/tool_runner.py  # 继承 Day58
src/customer_support/workflow.py  # 继承 Day56
tests/test_api.py  # 继承 Day61
tests/test_app.py  # 继承 Day51
tests/test_application.py  # 本日变更
tests/test_assistant.py  # 继承 Day51
tests/test_conversation.py  # 继承 Day55
tests/test_evaluation.py  # 继承 Day53
tests/test_idempotency.py  # 本日变更
tests/test_ingestion.py  # 继承 Day52
tests/test_knowledge.py  # 继承 Day52
tests/test_orders.py  # 继承 Day57
tests/test_retrieval.py  # 继承 Day54
tests/test_thread_store.py  # 继承 Day60
tests/test_tickets.py  # 继承 Day59
tests/test_tool_runner.py  # 继承 Day58
tests/test_workflow.py  # 继承 Day56
```

## 4. 按顺序阅读和动手

1. 打开 `src/customer_support/api.py`：搜索并跟踪：`Service`、`Service.handle`、`ChatRequest`、`ChatResponse`、`create_app`。写出输入、输出、调用方和失败分支。
2. 打开 `src/customer_support/application.py`：搜索并跟踪：`ApplicationResult`、`SupportApplication`、`SupportApplication.handle`、`SupportApplication.ask`。写出输入、输出、调用方和失败分支。
3. 打开 `src/customer_support/bootstrap.py`：搜索并跟踪：`build_embeddings`、`build_chat_model`、`build_assistant`、`build_application`。写出输入、输出、调用方和失败分支。
4. 打开 `src/customer_support/idempotency.py`：搜索并跟踪：`IdempotencyConflict`、`IdempotencyStore`、`IdempotencyStore.execute`。写出输入、输出、调用方和失败分支。
5. 打开 `tests/test_application.py`：搜索并跟踪：`Assistant`、`Assistant.ask`、`test_retried_product_request_reuses_the_same_ticket`。写出输入、输出、调用方和失败分支。
6. 打开 `tests/test_idempotency.py`：搜索并跟踪：`test_write_runs_once_and_key_cannot_change_meaning`。写出输入、输出、调用方和失败分支。

动手时先写或修改测试，确认失败原因正确，再完成最小实现。对上表列出的关键继承文件，至少核对一次调用接口；它们虽未改动，却决定今天的新能力能否生效。

## 5. 还原并验收

```powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 62
cd .build\day62\customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
..\..\..\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
```

验收不是只看新增测试：还原后的项目会同时运行 Day51 到今天积累的全部测试，这才证明新改动没有破坏旧能力。

## 6. 今天不能夸大的边界

内存实现尚未处理多实例并发。把实际运行结果写入 `workbook.md`。
