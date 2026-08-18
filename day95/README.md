# Day95 · Agent 查 PostgreSQL：目录优先与执行计划门禁

不能让 Agent 直接把自然语言变成任意 SQL 并执行。今天优先使用服务端查询目录；即使是
只读查询，也校验表白名单、禁止注释/多语句/锁，并以 `EXPLAIN (FORMAT JSON)` 计划判断
高代价扫描。

## 今日交付

- `sql_guard.py`：只读 SQL 校验、角色受控查询目录和计划门禁。
- `tests/test_sql_guard.py`：验证写操作、CTE 绕过、未知查询和大范围顺扫都会被拒绝。

## 今日边界

计划门禁是最后保险，不是索引设计替代品。生产应从真实慢查询、统计信息和
`EXPLAIN ANALYZE` 出发优化；不要对不可信 SQL 直接执行 `EXPLAIN ANALYZE`。
