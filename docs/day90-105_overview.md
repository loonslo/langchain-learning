# Day90–105 · 企业客服 Agent 进阶主线

这不是另一套玩具 demo。Day90 起新建 `enterprise_support` 项目，把 Day51–89 已有的
RAG、评测、LangGraph、MCP 基础向企业交付推进。它独立于现有 `customer_support/`，避免
覆盖历史课程或本地实验。

每一天只保存当日新增、修改的工程文件；使用下列命令重建对应日期的完整项目：

```bash
python tools/materialize_enterprise_day.py 105
cd .build/day105/enterprise-support
python -m pytest -q
```

## 路线

| 阶段 | Day | 交付 | 对应优先级 |
|---|---:|---|---|
| 对话业务契约 | 90 | few-shot 意图契约、枚举校验与拒绝未知意图 | 1 |
| 对话业务契约 | 91 | 槽位抽取、缺参追问、会话状态 | 1 |
| 对话业务契约 | 92 | 稳定 JSON：提取、schema 校验、一次受控修复 | 1 |
| 对话业务契约 | 93 | 把意图、槽位和人工转接接成显式工作流 | 1 |
| 真实数据层 | 94 | PostgreSQL schema、参数化仓储、RLS 租户边界 | 1 |
| 真实数据层 | 95 | Text2SQL 目录、只读校验、EXPLAIN 计划门禁 | 1 |
| 真实数据层 | 96 | Redis 租户版本缓存、限流与失效 | 1 |
| 向量与交付 | 97 | pgvector / Qdrant / Milvus 的可解释选型；Qdrant 租户过滤 | 1、3 |
| 向量与交付 | 98 | Postgres + Redis + Qdrant Compose、健康检查、Linux 运维手册 | 1、3 |
| 本地模型服务 | 99 | OpenAI 兼容 Provider 契约与 vLLM 配置边界 | 2 |
| 本地模型服务 | 100 | vLLM 启动命令、GPU 配置与容器 Profile | 2 |
| 本地模型服务 | 101 | p95/吞吐基准、量化和 KV Cache 的决策证据 | 2 |
| 企业协议 | 102 | MCP HTTP 鉴权：audience、scope、写工具审批 | 4 |
| 企业协议 | 103 | A2A Agent Card、任务状态与幂等任务仓储 | 4 |
| 企业协议 | 104 | A2A JSON-RPC / SSE HTTP 边界 | 4 |
| 企业协议 | 105 | 客服 Agent 调用订单 Agent 的集成验收与交付说明 | 4 |

## 不夸大的边界

- Compose 是本地可复现环境，不等于生产 Kubernetes 或 ACK 发布。
- 课程提供 PostgreSQL、Redis、Qdrant 和 vLLM 的真实接口与配置；测试使用替身，避免
  没有 Docker、GPU 或模型时无法学习。
- MCP 的 OAuth issuer 和企业 IdP、A2A 的远端服务均是部署时提供的外部依赖；课程实现
  resource-server / protocol 边界，而不是伪造身份系统。
- Milvus 在本课程中用于选型与部署边界对比，不重复再实现一套向量存储。职位明确要求
  Milvus 时，再把 Day97 的 `VectorStore` 适配器换成 Milvus 实现并压测。
