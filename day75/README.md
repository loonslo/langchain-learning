# Day75 · 备份与恢复验证

> 今天解决：有备份文件不代表能恢复。
>
> 第一性原则：恢复后必须做完整性和业务数据验证。

## 1. 与 Day74 的文件衔接

先还原并跑通 Day74，再开始今天。不要只看新增文件：先确认今天修改了哪些旧文件，再沿“关键继承文件”检查新能力是否真的进入已有产品链。

### 今天新增、修改或删除

| 项目相对路径 | 状态 | 为什么今天要看 |
|---|---|---|
| `src/customer_support/backup.py` | 新增 | 备份恢复 |
| `tests/test_backup.py` | 新增 | 验证今天新增能力的正向和失败路径 |
| `tests/test_thread_backup.py` | 新增 | 验证今天新增能力的正向和失败路径 |
| `src/customer_support/runtime.py` | 修改旧文件（上一版 Day73） | 真实依赖与最终 API 组合入口 |
| `src/customer_support/thread_store.py` | 修改旧文件（上一版 Day60） | SQLite 会话 |

### 关键继承文件

| 项目相对路径 | 状态 | 在今天链路中的作用 |
|---|---|---|
| `src/customer_support/api.py` | 继承 Day64，今天仍被变更代码调用 | HTTP 契约 |
| `src/customer_support/auth.py` | 继承 Day63，今天仍被变更代码调用 | JWT 身份 |
| `src/customer_support/bootstrap.py` | 继承 Day74，今天仍被变更代码调用 | 创建真实依赖并接入正式主链 |
| `src/customer_support/feedback.py` | 继承 Day73，今天仍被变更代码调用 | 反馈队列 |
| `src/customer_support/settings.py` | 继承 Day60，今天仍被变更代码调用 | 截至今天的运行路径与环境配置 |
| `src/customer_support/sync.py` | 继承 Day71，今天仍被变更代码调用 | 增量同步计划 |

运行 `python tools/day_change_report.py 75` 可查看全部“继承未改”文件。

## 2. 今天结束后的真实调用链

```text
正式 thread_db_path → SQLiteThreadStore.backup_to → integrity_check
```

验收时必须能指出：新增能力从哪里被调用、结果交给谁、失败会在哪一层被拦住。

## 3. Day75 结束后的完整项目结构

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
src/customer_support/api.py  # 继承 Day64
src/customer_support/app.py  # 继承 Day55
src/customer_support/application.py  # 继承 Day62
src/customer_support/assistant.py  # 继承 Day51
src/customer_support/auth.py  # 继承 Day63
src/customer_support/backup.py  # 本日变更
src/customer_support/bootstrap.py  # 继承 Day74
src/customer_support/cache.py  # 继承 Day68
src/customer_support/capacity.py  # 继承 Day72
src/customer_support/conversation.py  # 继承 Day60
src/customer_support/evaluation.py  # 继承 Day69
src/customer_support/feedback.py  # 继承 Day73
src/customer_support/idempotency.py  # 继承 Day62
src/customer_support/ingestion.py  # 继承 Day52
src/customer_support/knowledge.py  # 继承 Day54
src/customer_support/observability.py  # 继承 Day67
src/customer_support/orders.py  # 继承 Day57
src/customer_support/privacy.py  # 继承 Day66
src/customer_support/providers.py  # 继承 Day74
src/customer_support/quality_gate.py  # 继承 Day69
src/customer_support/readiness.py  # 继承 Day72
src/customer_support/retrieval.py  # 继承 Day54
src/customer_support/runtime.py  # 本日变更
src/customer_support/security.py  # 继承 Day65
src/customer_support/settings.py  # 继承 Day60
src/customer_support/sync.py  # 继承 Day71
src/customer_support/thread_store.py  # 本日变更
src/customer_support/tickets.py  # 继承 Day59
src/customer_support/tool_runner.py  # 继承 Day58
src/customer_support/vector_store.py  # 继承 Day71
src/customer_support/workflow.py  # 继承 Day65
tests/test_api.py  # 继承 Day64
tests/test_app.py  # 继承 Day51
tests/test_application.py  # 继承 Day68
tests/test_assistant.py  # 继承 Day51
tests/test_auth.py  # 继承 Day63
tests/test_backup.py  # 本日变更
tests/test_cache.py  # 继承 Day68
tests/test_capacity.py  # 继承 Day72
tests/test_conversation.py  # 继承 Day55
tests/test_evaluation.py  # 继承 Day53
tests/test_feedback.py  # 继承 Day73
tests/test_feedback_api.py  # 继承 Day73
tests/test_idempotency.py  # 继承 Day62
tests/test_ingestion.py  # 继承 Day52
tests/test_knowledge.py  # 继承 Day52
tests/test_observability.py  # 继承 Day67
tests/test_orders.py  # 继承 Day57
tests/test_privacy.py  # 继承 Day66
tests/test_providers.py  # 继承 Day74
tests/test_quality_gate.py  # 继承 Day69
tests/test_quality_gate_integration.py  # 继承 Day69
tests/test_readiness.py  # 继承 Day70
tests/test_release_readiness.py  # 继承 Day72
tests/test_retrieval.py  # 继承 Day54
tests/test_security.py  # 继承 Day65
tests/test_sync.py  # 继承 Day64
tests/test_sync_vector_store.py  # 继承 Day71
tests/test_thread_backup.py  # 本日变更
tests/test_thread_store.py  # 继承 Day60
tests/test_tickets.py  # 继承 Day59
tests/test_tool_runner.py  # 继承 Day58
tests/test_vector_store_contract.py  # 继承 Day71
tests/test_workflow.py  # 继承 Day56
```

## 4. 按顺序阅读和动手

1. 打开 `src/customer_support/runtime.py`：搜索并跟踪：`create_runtime_api`、`backup_threads`。写出输入、输出、调用方和失败分支。
2. 打开 `src/customer_support/thread_store.py`：搜索并跟踪：`Message`、`SQLiteThreadStore`、`SQLiteThreadStore.append`、`SQLiteThreadStore.load`、`SQLiteThreadStore.backup_to`。写出输入、输出、调用方和失败分支。
3. 打开 `src/customer_support/backup.py`：搜索并跟踪：`backup`、`integrity`。写出输入、输出、调用方和失败分支。
4. 打开 `tests/test_backup.py`：搜索并跟踪：`test_backup_is_actually_readable`。写出输入、输出、调用方和失败分支。
5. 打开 `tests/test_thread_backup.py`：搜索并跟踪：`test_the_product_thread_store_creates_a_verified_backup`。写出输入、输出、调用方和失败分支。

动手时先写或修改测试，确认失败原因正确，再完成最小实现。对上表列出的关键继承文件，至少核对一次调用接口；它们虽未改动，却决定今天的新能力能否生效。

## 5. 还原并验收

```powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 75
cd .build\day75\customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
..\..\..\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
```

验收不是只看新增测试：还原后的项目会同时运行 Day51 到今天积累的全部测试，这才证明新改动没有破坏旧能力。

## 6. 今天不能夸大的边界

本地 SQLite 演练不等于云数据库灾备。把实际运行结果写入 `workbook.md`。
