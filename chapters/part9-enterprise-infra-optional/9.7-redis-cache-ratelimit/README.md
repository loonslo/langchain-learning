# 9.7 Redis 缓存与限流：先定义失效条件

[全书目录](../../README.md) · [上一章 9.6](../9.6-readonly-sql-explain/README.md) · [下一章 9.8](../9.8-vectorstore-selection/README.md)

- **目标**：Redis 只做可失效的缓存与限流，不当数据库用：缓存键必须含租户、ACL/知识版本、模型和规范化问题，身份或知识变化后旧答案不能继续命中。
- **前置**：9.6（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.7-redis-cache-ratelimit`，进入 `.build/enterprise/9.7-redis-cache-ratelimit/enterprise-support` 后运行 `python -m pytest -q`

## 问题

上一版政策的回答不能在更新后继续缓存给用户，其他租户也不能命中这份结果。缓存范围与版本先定义好，Redis 才能作为安全的加速层。

## 概念

CacheScope 包含租户和版本边界；TTL 控制过期；限流限制一定窗口内的调用。`acl_version` 必须能区分不同权限视图（例如角色集合的哈希），否则权限不同的用户会共用同一条缓存答案。缓存可失效，业务真相不能只保存在缓存里。

## 流程

1. 根据可信身份和知识配置构建键。
2. 读取或写入带 TTL 的结果。
3. 执行窗口限流。
4. Redis 不可用时：限流失败关闭（抛 `RuntimeError`）；缓存读写目前直接抛出原始异常，是否降级为未命中由调用方决定。

## 本章交付

- `redis_store.py`：TTL 缓存和固定窗口限流的 Redis 契约。
- `tests/test_redis_store.py`：验证租户隔离、版本失效和 Redis 故障不放开限流。

## 代码导读

redis_store.py 先读 CacheScope 与 RedisAnswerCache，再读 FixedWindowRateLimiter 的计数和失效行为。

实现文件：

- [redis_store.py](src/enterprise_support/redis_store.py)

## 练习

保持问题相同但改变租户或知识版本，预测缓存是否命中；模拟 Redis 故障，检查限流是否被意外放开。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.7-redis-cache-ratelimit
cd .build/enterprise/9.7-redis-cache-ratelimit/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

离线替身验证协议与边界，不代表真实 Redis 并发、原子性和容量已通过验收。

生产可改为滑动窗口、令牌桶或网关限流；无论算法如何，Redis 故障时不得静默允许无限请求。
