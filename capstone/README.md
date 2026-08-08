# 多租户企业客服与工单 Copilot（Day51–78 主项目）

> 从项目立项、RAG MVP、企业权限、受控工具、持久化审批和长期记忆，一直走到评测、CI、监控、迁移、压测、部署与项目交接。当前是生产导向的本地原型，没有已验证的公网部署。
>
> 产品需求见 [`docs/project_brief.md`](docs/project_brief.md)，完整 Day51–78 路线见 [`docs/day51-78-roadmap.md`](docs/day51-78-roadmap.md)。

## 能力一览

| 模块 | 文件 | 整合自 |
|------|------|--------|
| 稳定业务契约 + 唯一服务入口 | `contracts.py` / `service.py` | Day51/58 |
| 文档处理 + 混合检索 + 溯源 | `knowledge_base.py` | day12–17 |
| 真实数据接入 + 增量同步 | `connector.py` | day54 |
| 查询前 ACL + 缺省拒绝 | `permissions.py` / `knowledge_base.py` | day55 |
| 上下文预算 + 不可信资料封装 | `context.py` | Day57 |
| JWT + 物理租户隔离 + Redis 限流 | `auth.py` | day56 |
| 受控业务查询 | `query_catalog.py` | Day61 |
| 持久化高风险审批 | `approval.py` | Day63 |
| 显式同意的长期偏好 | `memory.py` | Day64 |
| 输入输出内容安全 | `content_safety.py` | Day65 |
| 自动化评测（指标 + 报告 + 失败库） | `evaluation.py` | day18–27 |
| CI 评测门禁 | `ci_gate.py` | day58 |
| p95/p99 + token/成本 + request_id | `monitoring.py` / `monitoring_cli.py` | Day67 |
| pgvector 迁移能力 | `vector_store_pg.py` | Day68 |
| 容量与 SLO 验证 | `load_test.py` | Day69 |
| 部署和证据审计 | `deployment_check.py` / `evidence_audit.py` | Day70/75 |
| 统一认证 HTTP 服务 | `api_enterprise.py` | day41/44/45/56 |
| 输入边界 + PII 脱敏 | `security.py` | day47/65 |
| 权限与知识版本感知缓存 | `cache.py` | day43 |
| pytest 回归 | `test_regression.py` | day48 |
| Web 界面（演示） | `app_streamlit.py` | — |
| CLI 入口 | `main.py` | — |

## 架构与依赖方向

```text
HTTP / CLI / Evaluation
          │
          ▼
   AssistantService  ← 唯一业务入口
     │    │    │
     │    │    └─ ApprovalWorkflow / PreferenceMemory
     │    └────── CatalogQueryTool（可信 query_id）
     └─────────── KnowledgeBase
                       │
             ACL → Hybrid Retrieval → Context Budget

横切能力：JWT、内容安全、缓存、指标、trace、CI 和部署证据
```

## 快速开始

```bash
# 1) 使用项目虚拟环境安装锁定依赖
python -m pip install -r requirements-dev.txt

# 2) 复制配置模板，只填自己的本地地址/密钥；不要提交 .env
copy .env.example .env

# 3) 把公开文档放进 capstone/docs/（已带示例）
#    私有租户文档放 capstone/data/tenants/<tenant-key>/docs/

# 4) 建知识库
python -m capstone.main build

# 5) 提问
python -m capstone.main ask "RAG 为什么能减少幻觉？"

# 6) 跑评测
python -m capstone.main eval

# 查看任意一天在同一项目中的状态、证据和验收命令
python -m capstone.milestones 58
python -m capstone.milestones --json

# 每天的学习从对应任务文件开始；它会列出编码任务、失败测试和验收边界
python day58_unified_service_reliability.py --strict

# 7) 先跑不调用 LLM 的生产边界测试，再按需跑真实模型回归
pytest capstone/test_production.py -q
pytest capstone/test_regression.py -v

# 8) 本地需要登录演示时显式设置 CAPSTONE_ENABLE_DEV_LOGIN=true
uvicorn capstone.api_enterprise:app --reload
streamlit run capstone/app_streamlit.py
```

每日教程还会输出前置知识、术语白话解释、代码阅读顺序、逐步实验、预期现象、常见错误和复盘题。`--strict` 只检查当天依赖的项目证据是否存在；真正完成当天仍要执行输出中的验收命令，并理解负向测试为什么失败。

统一接口 `POST /v1/chat` 默认执行知识问答，也支持显式模式：

- `mode=memory`：设置、查看或删除受控偏好；普通对话不会被静默长期保存。
- `mode=data_query` + `query_id`：只执行服务端 catalog 中的只读查询。
- `mode=action` + `action=publish_reply`：创建持久化审批，主管通过 `/v1/approvals/{id}/decision` 一次性决策。

## 工程化要点（面试可讲）

- **检索质量**：向量召回 + BM25 关键词召回融合，专有名词不漏；metadata 溯源，答案标来源。
- **质量护城河**：评测集 = 回归用例库；拒答正确率量化防幻觉；失败用例库归档错因（检索没召回 vs 召回了生成错）。
- **安全**：租户物理分库、Chroma 查询前 ACL、缺 ACL 默认拒绝；输入边界和响应脱敏不替代授权。
- **认证**：开发使用短期本地 token；生产强制外部 JWT 密钥与 Redis 限流，建议接 IdP/JWKS。
- **可观测**：request_id 进入 LangChain metadata；指标仅保存问题指纹，不保存明文问题。
- **可复现**：被测链 `temperature=0`，回归断言用"含关键词/是否拒答"宽松匹配，避开随机性。

## 每日学习入口与项目运行入口

```text
# 每日文件保存当天任务，capstone/ 保存逐日累积的业务实现
PyCharm 主程序模块：customer_support.app
PyCharm 测试目录：tests
```

```bash
# 汇总查看全部 Day51–78 的接入状态；partial 不包装成已交付
python -m capstone.milestones --strict-evidence

# 项目基线、证据审计、监控和 provider 契约
python -m capstone.project_baseline --json
python -m capstone.evidence_audit
python -m capstone.monitoring_cli --json
python -m capstone.provider_contract

# 内容安全已经进入真实 API 请求路径；生产必须注入外部审核器
pytest capstone/test_production.py -q

# pgvector 是可选后端；先看迁移模板，再按需安装和配置
python -m capstone.vector_store_pg migration
python -m pip install -r requirements-pgvector.txt

# Bedrock provider 需要可选适配包
python -m pip install -r requirements-bedrock.txt

# 不调用 DeepSeek 的本地压测；real 模式从 LOADTEST_BEARER_TOKEN 读 token
python -m capstone.load_test --fake --users 10 --time 30s
```

证据审计会把缺少截图/GIF 报为警告。不要把 Dockerfile、迁移模板或本地演示表述成“已经公网部署”“已完成 pgvector 迁移”或“已满足全部合规要求”。Day51–78 的顶层文件是最新每日任务，不承载另一套业务实现；最终产品代码以 `capstone/` 为准。
