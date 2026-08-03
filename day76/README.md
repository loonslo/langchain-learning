# Day76 · 统一业务应用

> 今天解决：组件存在但没有形成一个请求链路。
>
> 第一性原则：安全、权限、缓存、工具、工单必须由统一入口编排。

## 1. 与前一天的关系

先还原并跑通 Day75，再开始今天。Day76 目录只保存今天新增或修改的完整文件；下方结构图中的“继承 DayNN”文件今天无需重复阅读。

## 2. 今天新增或修改

| 项目相对路径 | 变更 | 职责 |
|---|---|---|
| `src/customer_support/api.py` | 修改（上一版 Day61） | HTTP 契约 |
| `src/customer_support/application.py` | 新增 | 统一业务编排 |
| `src/customer_support/runtime.py` | 新增 | 真实依赖与最终 API 组合入口 |
| `tests/test_api.py` | 修改（上一版 Day61） | 验证今天新增能力的正向和失败路径 |
| `tests/test_application.py` | 新增 | 验证今天新增能力的正向和失败路径 |

## 3. Day76 结束后的完整项目结构

```text
.dockerignore  # 继承 Day70
.env.example  # 继承 Day51
Dockerfile  # 继承 Day70
data/eval_cases.json  # 继承 Day53
data/knowledge/customer_faq.md  # 继承 Day51
data/knowledge/refund.md  # 继承 Day52
data/knowledge/shipping.md  # 继承 Day52
deployment/pgvector_schema.sql  # 继承 Day71
pyproject.toml  # 继承 Day63
src/customer_support/__init__.py  # 继承 Day51
src/customer_support/api.py  # 本日变更
src/customer_support/application.py  # 本日变更
src/customer_support/assistant.py  # 继承 Day51
src/customer_support/auth.py  # 继承 Day63
src/customer_support/backup.py  # 继承 Day75
src/customer_support/bootstrap.py  # 继承 Day51
src/customer_support/cache.py  # 继承 Day68
src/customer_support/capacity.py  # 继承 Day72
src/customer_support/cli.py  # 继承 Day51
src/customer_support/conversation.py  # 继承 Day55
src/customer_support/evaluation.py  # 继承 Day53
src/customer_support/feedback.py  # 继承 Day73
src/customer_support/idempotency.py  # 继承 Day62
src/customer_support/ingestion.py  # 继承 Day52
src/customer_support/knowledge.py  # 继承 Day51
src/customer_support/observability.py  # 继承 Day67
src/customer_support/orders.py  # 继承 Day57
src/customer_support/privacy.py  # 继承 Day66
src/customer_support/providers.py  # 继承 Day74
src/customer_support/quality_gate.py  # 继承 Day69
src/customer_support/readiness.py  # 继承 Day70
src/customer_support/retrieval.py  # 继承 Day54
src/customer_support/runtime.py  # 本日变更
src/customer_support/security.py  # 继承 Day65
src/customer_support/settings.py  # 继承 Day51
src/customer_support/sync.py  # 继承 Day64
src/customer_support/thread_store.py  # 继承 Day60
src/customer_support/tickets.py  # 继承 Day59
src/customer_support/tool_runner.py  # 继承 Day58
src/customer_support/vector_store.py  # 继承 Day71
src/customer_support/workflow.py  # 继承 Day56
tests/test_api.py  # 本日变更
tests/test_application.py  # 本日变更
tests/test_assistant.py  # 继承 Day51
tests/test_auth.py  # 继承 Day63
tests/test_backup.py  # 继承 Day75
tests/test_cache.py  # 继承 Day68
tests/test_capacity.py  # 继承 Day72
tests/test_conversation.py  # 继承 Day55
tests/test_evaluation.py  # 继承 Day53
tests/test_feedback.py  # 继承 Day73
tests/test_idempotency.py  # 继承 Day62
tests/test_ingestion.py  # 继承 Day52
tests/test_knowledge.py  # 继承 Day51
tests/test_observability.py  # 继承 Day67
tests/test_orders.py  # 继承 Day57
tests/test_privacy.py  # 继承 Day66
tests/test_providers.py  # 继承 Day74
tests/test_quality_gate.py  # 继承 Day69
tests/test_readiness.py  # 继承 Day70
tests/test_retrieval.py  # 继承 Day54
tests/test_security.py  # 继承 Day65
tests/test_sync.py  # 继承 Day64
tests/test_thread_store.py  # 继承 Day60
tests/test_tickets.py  # 继承 Day59
tests/test_tool_runner.py  # 继承 Day58
tests/test_vector_store_contract.py  # 继承 Day71
tests/test_workflow.py  # 继承 Day56
```

## 4. 按顺序阅读和动手

1. 打开 `src/customer_support/api.py`：搜索并跟踪：`Application`、`Application.handle`、`ChatRequest`、`ChatResponse`、`create_app`。写出输入、输出、调用方和失败分支。
2. 打开 `src/customer_support/application.py`：搜索并跟踪：`ApplicationResult`、`SupportApplication`、`SupportApplication.handle`。写出输入、输出、调用方和失败分支。
3. 打开 `src/customer_support/runtime.py`：搜索并跟踪：`create_runtime_api`。写出输入、输出、调用方和失败分支。
4. 打开 `tests/test_api.py`：搜索并跟踪：`FakeApplication`、`FakeApplication.handle`、`test_api_uses_signed_identity_and_returns_final_contract`、`test_api_rejects_missing_identity_before_business_call`。写出输入、输出、调用方和失败分支。
5. 打开 `tests/test_application.py`：搜索并跟踪：`A`、`A.ask`、`test_end_to_end_order_is_scoped_and_unknown_question_escalates`。写出输入、输出、调用方和失败分支。

动手时先写/修改测试，确认失败原因正确，再完成最小实现。不要读取本日未修改的继承文件，除非测试失败需要沿调用链排查。

## 5. 还原并验收

```powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 76
cd .build\day76\customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
..\..\..\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
```

验收不是只看新增测试：还原后的项目会同时运行 Day51 到今天积累的全部测试，这才证明新改动没有破坏旧能力。

## 6. 今天不能夸大的边界

仍是本地同步实现。把实际运行结果写入 `workbook.md`。
