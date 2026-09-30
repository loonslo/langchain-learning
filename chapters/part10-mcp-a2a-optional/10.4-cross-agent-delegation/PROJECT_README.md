# 企业客服 Agent 进阶项目（章节 9.1–10.4）

## 能力链

```text
用户问题
  → few-shot 意图契约 → 槽位状态机 → 缺参追问 / 人工转接
  → PostgreSQL（RLS 会话真相源）+ Redis（缓存/限流）
  → Qdrant（tenant filter 检索） → OpenAI-compatible / vLLM 模型服务
  → MCP resource-server 授权企业工具
  → A2A 客服 Agent 委托订单 Agent（Task + JSON-RPC + SSE）
```

## 本地学习

```bash
python tools/materialize.py enterprise 10.4-cross-agent-delegation
cd .build/enterprise/10.4-cross-agent-delegation/enterprise-support
python -m pytest -q
cp .env.example .env
docker compose up -d
```

GPU 模型服务为可选 profile：先填写 `MODEL_ID`、`VLLM_API_KEY` 和显存配置，再执行：

```bash
docker compose -f compose.yaml -f compose.vllm.yaml --profile gpu up -d
```

每次更换模型、量化方式、检索后端或 prompt，都应重跑客服意图、RAG、JSON、工具安全和延迟 SLO 回归；不要因为端口健康就跳过质量验证。
