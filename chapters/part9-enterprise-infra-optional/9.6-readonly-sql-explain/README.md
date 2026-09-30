# 9.6 只读查询目录与执行计划：安全也包括成本

[全书目录](../../README.md) · [上一章 9.5](../9.5-postgres-rls/README.md) · [下一章 9.7](../9.7-redis-cache-ratelimit/README.md)

- **目标**：不能让 Agent 把自然语言直接变成任意 SQL 并执行：优先用服务端查询目录，并校验只读、表白名单和 `EXPLAIN (FORMAT JSON)` 执行计划的代价。
- **前置**：9.5（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.6-readonly-sql-explain`，进入 `.build/enterprise/9.6-readonly-sql-explain/enterprise-support` 后运行 `python -m pytest -q`

## 问题

即使 SQL 不写数据，扫描整张大表也可能拖垮服务。查询目录固定已批准的业务查询，执行计划检查帮助限制意外代价。

## 概念

QueryCatalog 保存受控查询；只读校验限制语句形状；EXPLAIN 提供计划；预算门禁检查扫描代价。权限与成本分别有独立检查。

## 流程

1. `QueryCatalog.get(query_id, roles)` 按 id 取出已批准的查询：未知 id 抛 `SqlPolicyError`，角色不匹配抛 `PermissionError`。
2. 取出的 SQL 经 `validate_read_only_sql`：以 SELECT/WITH 开头、无多语句和注释、无写入或加锁关键字、表在白名单内、带 LIMIT。
3. 调用方用数据库驱动的占位符（如 `%s`）绑定参数，并对同一条 SQL 执行 `EXPLAIN (FORMAT JSON)`；本模块不连接数据库。
4. 把 EXPLAIN 结果交给 `reject_expensive_plan`：出现超过 `max_seq_rows` 的顺序扫描就抛 `SqlPolicyError`；通过后才真正执行。

## 本章交付

- `sql_guard.py`：只读 SQL 校验、角色受控查询目录和计划门禁。
- `tests/test_sql_guard.py`：验证写操作、CTE 绕过、多语句、未知查询、未授权角色和大范围顺扫都会被拒绝。

## 代码导读

sql_guard.py 先读 validate_read_only_sql，再读 CatalogQuery、QueryCatalog 与 reject_expensive_plan。

实现文件：

- [sql_guard.py](src/enterprise_support/sql_guard.py)

## 练习

比较允许查询、未知查询和带多语句的输入；构造高代价计划，说明只读为何仍可能被拒绝。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.6-readonly-sql-explain
cd .build/enterprise/9.6-readonly-sql-explain/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

合成计划验证规则，不能替代真实数据库的角色限制、超时与成本测量。

计划门禁是最后保险，不是索引设计替代品。生产应从真实慢查询、统计信息和 `EXPLAIN ANALYZE` 出发优化；不要对不可信 SQL 直接执行 `EXPLAIN ANALYZE`。
