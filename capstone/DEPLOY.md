# 真部署：拿一个能点的公网地址（Day60）

> `docker run` 在本机起来 ≠ 上线。上线 = 有一个手机能打开的公网 URL。这份是把毕业项目部署出去的最小路径。**线上这一版用可公开语料**（自己写的 / 开源年报），真实脏数据只在本地跑——这是合规边界。

## 0. 部署前确认

- [ ] `.env` 里的 key 走环境变量注入，**不进镜像、不进仓库**。
- [ ] 线上知识库目录换成可公开语料。
- [ ] 接口在 `/v1` 下，OpenAPI 文档 `/docs` 能打开（Day66）。
- [ ] 存活检查 `/live` 返回 200，依赖检查 `/ready` 返回 `ready`。
- [ ] 生产环境已配置外部内容安全服务；审核服务不可用时请求会按 fail-closed 拒绝。

## 1. 本地容器先跑通

```bash
docker build --pull -t kb-agent .
# 生产配置至少要有 JWT_SECRET、REDIS_URL、CONTENT_SAFETY_URL、模型地址/密钥和 embedding 路径。
# /var/lib/capstone 必须挂持久卷：知识库、同步状态、记忆和审批记录都不能只存在容器临时层。
# Windows 容器访问宿主本地模型时，base URL 通常使用 host.docker.internal。
docker run --rm -p 8000:8000 --env-file .env \
  -v capstone-data:/var/lib/capstone kb-agent
# 开 http://127.0.0.1:8000/docs 验证
```

## 2. 选一个云平台（按省事排序）

| 平台 | 特点 | 适合 |
|------|------|------|
| Render | 连 GitHub 自动构建，免费档够 demo | 最省事，推荐先用这个 |
| Fly.io | `fly launch` 一条命令，全球边缘 | 想要低延迟 |
| 云主机（轻量服务器） | 自己装 Docker，最自由 | 想完整掌控 / 已有机器 |

### Render 最小步骤
1. 仓库根放 `Dockerfile`（从 `Dockerfile.example` 改 CMD）。
2. Render 新建 Web Service，连这个 repo。
3. 在平台密钥管理中配置 `JWT_SECRET`、`REDIS_URL`、`CONTENT_SAFETY_URL`、模型地址/密钥和 embedding 路径。
4. 挂载持久卷到 `/var/lib/capstone`；需要数据查询或动作审批时，再显式启用对应 feature flag。
5. Health Check Path 填 `/live`，部署流水线另行轮询 `/ready`。
6. 部署完拿到 `https://xxx.onrender.com`，手机开 `/docs` 验证。

### Fly.io 最小步骤
```bash
fly launch          # 自动识别 Dockerfile，生成 fly.toml
fly secrets set DEEPSEEK_API_KEY=xxx EMBED_MODEL_PATH=xxx \
  JWT_SECRET=xxx REDIS_URL=xxx CONTENT_SAFETY_URL=https://moderator.example.com/check
fly deploy
fly open            # 打开公网地址
```

## 3. 上线后自检（对应最终验收闸门第 6 条）

- [ ] 公网 URL 手机能打开。
- [ ] `/docs` 显示 `/v1` 接口。
- [ ] 无 token 调 `/v1/chat` → 401；登录拿 token 后能正常问答。
- [ ] `/live` 返回 200，`/ready` 返回 ready；故意断开 Redis 或审核服务时，`/ready` 能暴露故障。
- [ ] 仓库里没有任何 key（`git log -p | grep -i key` 自查一遍）。

## 4. 常见坑

- **embedding 模型太大进不了免费档**：本地 bge 模型几百 MB，免费容器内存可能不够。线上可改用云 embedding API，或选更小的模型，本地仍用 bge。
- **首次冷启动慢**：建库 + load 模型耗时，加个启动预热或把 Chroma 落盘后随镜像带上。
- **多 worker 限流**：生产必须配置 Redis；未配置时应用拒绝启动，而不是静默退回内存限流。
- **内容审核不是字符串黑名单**：生产必须连接可审计的外部审核服务；服务超时或返回异常时默认拒绝请求。
- **动作与查询默认关闭**：只有准备好查询目录、审批人和持久化数据库后，才启用 `ENABLE_QUERY_TOOL`、`ENABLE_ACTIONS`。
- **本地模型不可达**：容器内的 `127.0.0.1` 是容器自身；改用宿主可达地址或同网络模型服务。
