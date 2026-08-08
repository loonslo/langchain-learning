# Day61 · FastAPI 服务边界

> 今天解决：命令行无法被前端或其他服务调用。
>
> 第一性原则：HTTP 层固定输入输出契约并复用业务入口。

## 1. 与 Day60 的文件衔接

先还原并跑通 Day60，再开始今天。不要只看新增文件：先确认今天修改了哪些旧文件，再沿“关键继承文件”检查新能力是否真的进入已有产品链。

### 今天新增、修改或删除

| 项目相对路径 | 状态 | 为什么今天要看 |
|---|---|---|
| `src/customer_support/api.py` | 新增 | HTTP 契约 |
| `src/customer_support/runtime.py` | 新增 | 真实依赖与最终 API 组合入口 |
| `tests/test_api.py` | 新增 | 验证今天新增能力的正向和失败路径 |
| `pyproject.toml` | 修改旧文件（上一版 Day56） | 截至今天的完整依赖与测试配置 |

### 关键继承文件

| 项目相对路径 | 状态 | 在今天链路中的作用 |
|---|---|---|
| `src/customer_support/application.py` | 继承 Day59，今天仍被变更代码调用 | 统一业务编排 |
| `src/customer_support/assistant.py` | 继承 Day51，今天仍被变更代码调用 | 检索、拒答、生成与来源返回 |
| `src/customer_support/bootstrap.py` | 继承 Day60，今天仍被变更代码调用 | 创建真实依赖并接入正式主链 |

运行 `python tools/day_change_report.py 61` 可查看全部“继承未改”文件。

## 2. 今天结束后的真实调用链

```text
HTTP /chat → create_app → application.handle → Day55–60 累积主链
```

验收时必须能指出：新增能力从哪里被调用、结果交给谁、失败会在哪一层被拦住。

## 3. Day61 结束后的完整项目结构

```text
.env.example  # 继承 Day51
data/eval_cases.json  # 继承 Day53
data/knowledge/customer_faq.md  # 继承 Day51
data/knowledge/refund.md  # 继承 Day52
data/knowledge/shipping.md  # 继承 Day52
pyproject.toml  # 本日变更
src/customer_support/__init__.py  # 继承 Day51
src/customer_support/api.py  # 本日变更
src/customer_support/app.py  # 继承 Day55
src/customer_support/application.py  # 继承 Day59
src/customer_support/assistant.py  # 继承 Day51
src/customer_support/bootstrap.py  # 继承 Day60
src/customer_support/conversation.py  # 继承 Day60
src/customer_support/evaluation.py  # 继承 Day53
src/customer_support/ingestion.py  # 继承 Day52
src/customer_support/knowledge.py  # 继承 Day54
src/customer_support/orders.py  # 继承 Day57
src/customer_support/retrieval.py  # 继承 Day54
src/customer_support/runtime.py  # 本日变更
src/customer_support/settings.py  # 继承 Day60
src/customer_support/thread_store.py  # 继承 Day60
src/customer_support/tickets.py  # 继承 Day59
src/customer_support/tool_runner.py  # 继承 Day58
src/customer_support/workflow.py  # 继承 Day56
tests/test_api.py  # 本日变更
tests/test_app.py  # 继承 Day51
tests/test_application.py  # 继承 Day60
tests/test_assistant.py  # 继承 Day51
tests/test_conversation.py  # 继承 Day55
tests/test_evaluation.py  # 继承 Day53
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
2. 打开 `src/customer_support/runtime.py`：搜索并跟踪：`create_runtime_api`。写出输入、输出、调用方和失败分支。
3. 打开 `tests/test_api.py`：搜索并跟踪：`Fake`、`Fake.ask`、`test_api_schema_and_validation`、`Product`、`Product.handle`、`test_api_calls_the_cumulative_product_not_a_new_chat_implementation`。写出输入、输出、调用方和失败分支。

动手时先写或修改测试，确认失败原因正确，再完成最小实现。对上表列出的关键继承文件，至少核对一次调用接口；它们虽未改动，却决定今天的新能力能否生效。

## 5. 还原并验收

```powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 61
cd .build\day61\customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
..\..\..\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
```

验收不是只看新增测试：还原后的项目会同时运行 Day51 到今天积累的全部测试，这才证明新改动没有破坏旧能力。

## 6. 今天不能夸大的边界

API 尚未认证。把实际运行结果写入 `workbook.md`。
