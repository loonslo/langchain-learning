# Day98 · Compose、本地 Linux 运维与可交付环境

今天把前三个真实依赖固定为一个本地交付单元：PostgreSQL 是真相源，Redis 是缓存/限流，
Qdrant 是检索后端。服务只绑定 loopback，默认不把数据库端口暴露到公网。

## 今日交付

- `compose.yaml`：Postgres、Redis、Qdrant 的本地可复现依赖。
- `ops/linux-compose.md`：Linux 主机部署、健康检查、备份和回滚步骤。
- `runtime.py`：启动前配置检查，防止带开发默认值上线。

## 验收

```bash
python tools/materialize_enterprise_day.py 98
cd .build/day98/enterprise-support
cp .env.example .env
docker compose up -d
docker compose ps
python -m pytest -q
```

## 今日边界

Compose 是单机交付起点，不是高可用方案；生产镜像必须锁定 digest，密钥由 Secret/密钥
管理服务注入，而不是保存在 `.env`。
