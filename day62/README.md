# Day62 · 写操作幂等

> 今天解决：客户端重试可能创建重复工单。
>
> 第一性原则：同一幂等键和请求只能执行一次。

## 1. 与前一天的关系

先还原并跑通 Day61，再开始今天。Day62 目录只保存今天新增或修改的完整文件；下方结构图中的“继承 DayNN”文件今天无需重复阅读。

## 2. 今天新增或修改

| 项目相对路径 | 变更 | 职责 |
|---|---|---|
| `src/customer_support/idempotency.py` | 新增 | 写操作去重 |
| `tests/test_idempotency.py` | 新增 | 验证今天新增能力的正向和失败路径 |

## 3. Day62 结束后的完整项目结构

```text
.env.example  # 继承 Day51
data/eval_cases.json  # 继承 Day53
data/knowledge/customer_faq.md  # 继承 Day51
data/knowledge/refund.md  # 继承 Day52
data/knowledge/shipping.md  # 继承 Day52
pyproject.toml  # 继承 Day61
src/customer_support/__init__.py  # 继承 Day51
src/customer_support/api.py  # 继承 Day61
src/customer_support/assistant.py  # 继承 Day51
src/customer_support/bootstrap.py  # 继承 Day51
src/customer_support/cli.py  # 继承 Day51
src/customer_support/conversation.py  # 继承 Day55
src/customer_support/evaluation.py  # 继承 Day53
src/customer_support/idempotency.py  # 本日变更
src/customer_support/ingestion.py  # 继承 Day52
src/customer_support/knowledge.py  # 继承 Day51
src/customer_support/orders.py  # 继承 Day57
src/customer_support/retrieval.py  # 继承 Day54
src/customer_support/settings.py  # 继承 Day51
src/customer_support/thread_store.py  # 继承 Day60
src/customer_support/tickets.py  # 继承 Day59
src/customer_support/tool_runner.py  # 继承 Day58
src/customer_support/workflow.py  # 继承 Day56
tests/test_api.py  # 继承 Day61
tests/test_assistant.py  # 继承 Day51
tests/test_conversation.py  # 继承 Day55
tests/test_evaluation.py  # 继承 Day53
tests/test_idempotency.py  # 本日变更
tests/test_ingestion.py  # 继承 Day52
tests/test_knowledge.py  # 继承 Day51
tests/test_orders.py  # 继承 Day57
tests/test_retrieval.py  # 继承 Day54
tests/test_thread_store.py  # 继承 Day60
tests/test_tickets.py  # 继承 Day59
tests/test_tool_runner.py  # 继承 Day58
tests/test_workflow.py  # 继承 Day56
```

## 4. 按顺序阅读和动手

1. 打开 `src/customer_support/idempotency.py`：搜索并跟踪：`IdempotencyConflict`、`IdempotencyStore`、`IdempotencyStore.execute`。写出输入、输出、调用方和失败分支。
2. 打开 `tests/test_idempotency.py`：搜索并跟踪：`test_write_runs_once_and_key_cannot_change_meaning`。写出输入、输出、调用方和失败分支。

动手时先写/修改测试，确认失败原因正确，再完成最小实现。不要读取本日未修改的继承文件，除非测试失败需要沿调用链排查。

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
