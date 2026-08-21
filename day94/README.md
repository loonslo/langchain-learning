# Day94 · PostgreSQL 真实会话层与租户边界

SQLite 适合本地学习，不适合作为多副本服务的共享会话真相源。今天用 PostgreSQL schema、
参数化查询和 RLS 把会话数据的租户隔离落实到数据库层。

## 今日交付

- `deployment/postgres/001_support.sql`：会话表、索引、RLS 策略。
- `postgres.py`：只接受参数化 SQL 的会话仓储。
- `tests/test_postgres.py`：验证 `set_config` 租户上下文和参数没有拼进 SQL。

## 今日边界

应用层 tenant 校验和 RLS 都要保留。RLS 策略不会替代连接池、迁移、备份和慢查询治理。
