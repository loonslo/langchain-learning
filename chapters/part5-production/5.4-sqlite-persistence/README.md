# 5.4 SQLite 持久化：把问答变成可查询记录

[全书目录](../../README.md) · [上一章 5.3](../5.3-cost-cache-routing/README.md) · [下一章 5.5](../5.5-docker-packaging/README.md)

- **目标**：给 LLM 应用建一张可查询的对话日志表，并避开 SQLite 生产使用中的 6 个常见坑。
- **前置**：4.10。
- **环境**：离线，只用标准库的 SQLite。
- **命令**：`python tools/run_chapter.py 5.4`（数据库 `app.db` 写在本章目录）

## 问题

4.10 的 checkpoint 存的是“图状态”，用来恢复会话。业务上还需要一张可查询的日志表：谁在什么时候问了什么、用了哪个模型、花了多少钱、多久返回、失败没有、用户点没点踩。这张表是成本核算、失败分析和评测集回流的数据源。5.1 的 HTTP 服务就使用本章的数据层。

## 概念

- **为什么用 SQLite**：一个文件就是一个库，零部署，标准库自带，适合单机服务、内部工具和中小并发。
- **准确的边界**：不是“SQLite 不能上生产”，而是“SQLite 不能多机部署”。它支持多进程并发读，开 WAL 后读写不互相阻塞，真正的限制是同一时刻只有一个写事务，且锁基于文件；服务多副本部署（多个 pod 写同一个网络文件）时，文件锁在 NFS 上不可靠，会损坏数据。多副本部署是迁移到 PostgreSQL 最硬的触发条件，和数据量无关。选型的完整取舍见 [docs/legacy/ADR-001](../../../docs/legacy/ADR-001-对话日志存储选型.md)。
- **六个坑**：
  1. 连接泄漏：`with sqlite3.connect(...)` 只提交事务，不关连接。
  2. `database is locked`：默认 journal 模式下写阻塞读。
  3. 全表扫描：`WHERE user_id ORDER BY id` 没有索引。
  4. 表结构改不动：没有版本号，加字段靠手工 `ALTER`。
  5. 数据没法用：只存问答，算不出成本、查不出失败、导不出评测集。
  6. 分页漂移：`LIMIT/OFFSET` 在持续写入的表上会漏数据或重复，要用游标分页。
- **数据库路径用绝对路径**：相对路径跟着工作目录走，从不同位置运行会连到不同的文件，表现就是“数据莫名其妙丢了”。

## 流程

`sqlite_persistence.py` 的演示：`migrate()` 建表并升级 schema 版本 → `save_qa` 保存三条问答（含一条失败）→ `save_feedback` 记录点踩 → `get_history` 游标分页 → `daily_stats` 按天统计（请求数、失败率、成本、平均与 p95 延迟）→ `export_eval_set` 把被点踩或失败的记录导出成评测集。

## 代码导读

[sqlite_persistence.py](sqlite_persistence.py) 较长（约 530 行），按坑的编号阅读：【一】连接管理（`get_conn`、`tx`）→ 迁移（`migrate`）→ 读写函数（`save_qa`、`get_history`）→ 统计与导出（`daily_stats`、`export_eval_set`）→ `purge_old`。

## 练习

1. 运行两次，确认 `migrate()` 幂等；再用 `sqlite3` 命令行查看 `app.db` 里的表和索引。
2. 用两个线程同时写入，观察 `database is locked` 是否出现，以及 `BUSY_TIMEOUT_MS` 的作用。
3. 往 `get_history` 的数据里持续写入，对比游标分页与 `OFFSET` 分页的结果。
4. 说明在什么条件下应该迁移到 PostgreSQL（9.5）。

## 运行与边界

- `app.db` 和导出的 `eval_set_from_prod.json` 都在本章目录，已被 `.gitignore` 忽略。
- 日志里可能含用户的问题和回答，属于个人数据，需要脱敏和保留期限（见 5.7、`purge_old`）。
