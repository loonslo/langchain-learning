# 真部署：拿一个能点的公网地址（Day60）

> `docker run` 在本机起来 ≠ 上线。上线 = 有一个手机能打开的公网 URL。这份是把毕业项目部署出去的最小路径。**线上这一版用可公开语料**（自己写的 / 开源年报），真实脏数据只在本地跑——这是合规边界。

## 0. 部署前确认

- [ ] `.env` 里的 key 走环境变量注入，**不进镜像、不进仓库**。
- [ ] 线上知识库目录换成可公开语料。
- [ ] 接口在 `/v1` 下，OpenAPI 文档 `/docs` 能打开（Day66）。
- [ ] 健康检查 `/health` 返回 200（平台靠它判活）。

## 1. 本地容器先跑通

```bash
# 用企业版服务做镜像入口
cp ../requirements.example.txt requirements.txt
# Dockerfile 的 CMD 改成：
#   uvicorn capstone.api_enterprise:app --host 0.0.0.0 --port 8000
docker build -t kb-agent .
docker run -p 8000:8000 --env-file ../.env kb-agent
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
3. 在 Render 后台配环境变量：`DEEPSEEK_API_KEY`、`EMBED_MODEL_PATH` 等（**不写进仓库**）。
4. Health Check Path 填 `/health`。
5. 部署完拿到 `https://xxx.onrender.com`，手机开 `/docs` 验证。

### Fly.io 最小步骤
```bash
fly launch          # 自动识别 Dockerfile，生成 fly.toml
fly secrets set DEEPSEEK_API_KEY=xxx EMBED_MODEL_PATH=xxx
fly deploy
fly open            # 打开公网地址
```

## 3. 上线后自检（对应最终验收闸门第 6 条）

- [ ] 公网 URL 手机能打开。
- [ ] `/docs` 显示 `/v1` 接口。
- [ ] 无 token 调 `/v1/chat` → 401；登录拿 token 后能正常问答。
- [ ] `/health` 200。
- [ ] 仓库里没有任何 key（`git log -p | grep -i key` 自查一遍）。

## 4. 常见坑

- **embedding 模型太大进不了免费档**：本地 bge 模型几百 MB，免费容器内存可能不够。线上可改用云 embedding API，或选更小的模型，本地仍用 bge。
- **首次冷启动慢**：建库 + load 模型耗时，加个启动预热或把 Chroma 落盘后随镜像带上。
- **成本失控**：线上 demo 给 `/v1/chat` 配限流（Day56 已做），别让人刷爆你的 API 账单。
