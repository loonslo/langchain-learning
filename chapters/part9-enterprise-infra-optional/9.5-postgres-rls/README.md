# 9.5 PostgreSQL 与 RLS：数据库也要知道租户

[全书目录](../../README.md) · [上一章 9.4](../9.4-intent-workflow/README.md) · [下一章 9.6](../9.6-readonly-sql-explain/README.md)

- **目标**：用 PostgreSQL schema、参数化查询和 RLS 把会话数据的租户隔离落实到数据库层（SQLite 只适合本地学习，不适合多副本共享会话）。
- **前置**：9.4（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.5-postgres-rls`，进入 `.build/enterprise/9.5-postgres-rls/enterprise-support` 后运行 `python -m pytest -q`

## 问题

多副本服务需要共享会话数据。迁移数据库时，除了连接方式，还要让租户边界进入查询和数据库策略，避免只在界面上区分用户。

## 概念

参数化查询分离 SQL 与数据；RLS 在数据库中约束行访问；租户上下文与连接事务共同决定策略范围。

## 流程

1. 查看会话表和策略。
2. 为当前事务设置可信租户。
3. 通过仓储保存与读取消息：查询同时带 `tenant_id` 条件，读写结束都 `commit`，让租户设置随事务清除。
4. 验证相同线程名在不同租户下仍隔离。

## 本章交付

- `deployment/postgres/001_support.sql`：会话表、索引、RLS 策略。
- `postgres.py`：只接受参数化 SQL 的会话仓储。
- `tests/test_postgres.py`：验证 `set_config` 租户上下文、参数没有拼进 SQL、读查询带 `tenant_id` 且读完提交。

## 代码导读

先读 deployment/postgres/001_support.sql，再读 postgres.py 的 PostgresConversationStore 与连接边界。

实现文件：

- [postgres.py](src/enterprise_support/postgres.py)

## 练习

用离线连接替身确认参数传递；具备本地数据库后再以受控租户验证策略，区分仓储单测和真实 RLS 验收。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.5-postgres-rls
cd .build/enterprise/9.5-postgres-rls/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

当前离线测试不能证明数据库角色和 RLS 实际生效；真实 PostgreSQL 部署与凭据需要独立配置。

应用层 tenant 校验和 RLS 都要保留。RLS 策略不会替代连接池、迁移、备份和慢查询治理。
