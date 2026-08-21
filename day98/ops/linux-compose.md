# 单机 Linux 部署手册

1. 使用受支持的 Linux 发行版安装 Docker Engine 与 Compose plugin；应用账户加入 `docker`
   组前先评估该组等同高权限的风险。
2. 在受限目录放置仓库、生产 `.env` 和固定镜像 digest；`.env` 权限设为仅运行账户可读。
3. 执行 `docker compose --env-file .env pull`，审核镜像版本后执行
   `docker compose --env-file .env up -d`。
4. 用 `docker compose ps`、`docker compose logs --tail=100` 和各服务 healthcheck 验证；
   数据库端口保持 loopback 或仅在私有网络安全组中开放。
5. PostgreSQL 定时逻辑备份/物理备份并做恢复演练；Qdrant 可从源文档重建但仍需保存快照以
   缩短恢复时间；Redis 缓存可丢弃，限流配置不可依赖其永久保存。
6. 回滚使用上一个已验证镜像 digest 与数据库迁移的兼容策略，不能用“删除 volume”代替回滚。

上线前仍需补 TLS、反向代理、密钥管理、日志集中化、告警、容量测试和故障演练。
