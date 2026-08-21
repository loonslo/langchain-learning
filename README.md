# LangChain 学习记录 · 测试工程师转 AI 应用开发

> 循序渐进的每日代码：从"问一次"到"能查文档、能评测、能上线"，一天一个核心概念。
> 每个文件开头有「这天学什么」，关键行有注释，能独立运行。
> Day1–50 建立 AI 应用开发与评测底座；Day51–79 连续交付一个带浏览器前端的生产导向项目；Day80–89 把测试背景升级为 AI 质量工程能力；Day90–105 补齐企业数据、推理服务、MCP 鉴权与 A2A 多 Agent 集成。

## 环境

```bash
pip install langchain langchain-openai langchain-community python-dotenv \
            langchain-text-splitters faiss-cpu pypdf langchain-huggingface \
            langchain-chroma rank_bm25 \
            langgraph langsmith
```

> 说明：本仓库基于 **langchain 1.x / langgraph 1.x**。注意 v1 里部分检索器迁到了
> `langchain_classic`（day13/14/16 已用新路径）。公共配置（模型路径、LLM 工厂、
> temperature=0）统一在 `common.py`，换机器只改那一处或 `.env`。

`.env` 配置（用 DeepSeek，兼容 OpenAI 格式）：

```
DEEPSEEK_API_KEY=你的key
# 可选：开 LangSmith trace（day21）
# LANGSMITH_API_KEY=你的key
# 可选：覆盖默认本地模型路径
# EMBED_MODEL_PATH=...
# RERANKER_MODEL_PATH=...
```

RAG 部分需要本地中文 embedding 模型，推荐用魔搭 ModelScope 下载（免代理）：

```python
from modelscope import snapshot_download
print(snapshot_download('BAAI/bge-small-zh-v1.5'))  # 把路径填进各 RAG 文件的 MODEL_PATH
```

工程化阶段（Day41+）还需要：`pip install fastapi uvicorn pytest`
企业 / 上线阶段（Day56/63/66）还需要：`pip install "python-jose[cryptography]" langchain-postgres "psycopg[binary]" locust`

## 课程地图（Day1–Day105）

下表按学习阶段列出全部 Day 的入口、主题和验收目标；每个 Day 目录的 README 提供该日的运行方式与练习说明。

> Day1–50 使用按天归档的独立练习目录建立基础；Day51–78 使用“每日完整变更集”推进同一个项目，Day79 为该项目的独立浏览器前端。每天除了新增文件，还必须展示被改写的旧文件和继续参与主链但未改的文件。README 记录当天完整结构，未修改文件不重复复制，并可用 `tools/materialize_day.py` 还原 Day51–78 中任意一天。

### 阶段0 固本 + 裸写 harness（Day1-11）

| Day | 文件 | 概念 |
|-----|------|------|
| 1 | `day01/day01_first_chat.py` | 基础调用 + Prompt + LCEL 管道 |
| 2 | `day02/day02_control_output.py` | 控制输出：temperature + 流式 |
| 3 | `day03/day03_structured_output.py` | 结构化输出：Pydantic |
| 4 | `day04/day04_memory_chat.py` | 多轮记忆 |
| 5 | `day05/day05_tool_calling.py` | 工具调用 |
| 6 | `day06/day06_chatbot_project.py` | 综合项目：记忆+工具+多角色 |
| 7 | `day07/day07_rag_load_split.py` | RAG：加载 + 切割 |
| 8 | `day08/day08_rag_embed_retrieve.py` | RAG：向量化 + 检索 |
| 9 | `day09/day09_minimal_rag.py` | 最小 RAG：完整问答（MMR、拒答）+ 提示工程 |
| 10 | `day10/day10_raw_sdk_rag_agent_loop.py` | 裸 SDK 手写 RAG + agent loop（理解 harness）|
| 11 | `day11/day11_llm_principles.py` | LLM 原理认知（token/embedding/attention/幻觉）|

### 阶段1 RAG 进阶（Day12-17）

| Day | 文件 | 概念 |
|-----|------|------|
| 12 | `day12/day12_rag_pdf_sources.py` | 处理真实 PDF + 来源溯源 + 封装 |
| 13 | `day13/day13_rag_chunk_strategy.py` | chunk 策略对比 |
| 14 | `day14/day14_rag_hybrid_search.py` | 混合检索：向量 + BM25 |
| 15 | `day15/day15_rag_query_rewrite.py` | 查询改写：Multi-Query + HyDE + Context Engineering |
| 16 | `day16/day16_rag_chroma_persist.py` | 向量库持久化：Chroma |
| 17 | `day17/day17_rag_multimodal_rerank.py` | 多模态读图 + reranker |

### 阶段2 RAG + Agent 双评测 ★护城河（Day18-27）

| Day | 文件 | 概念 |
|-----|------|------|
| 18 | `day18/day18_eval_basics.py` | 评测集 + 手写三大指标 |
| 19 | `day19/day19_eval_llm_judge.py` | LLM-as-judge：正确性/忠实度 |
| 20 | `day20/day20_eval_dataset_build.py` | 造评测集（上）：schema + 事实/跨段落 |
| 21 | `day21/day21_eval_dataset_ragas.py` | 造评测集（下）：拒答/引用 + RAGAS/DeepEval |
| 22 | `day22/day22_langsmith_eval.py` | LangSmith trace + 在线评估 |
| 23 | `day23/day23_eval_regression_curve.py` | 评测集版本化 + 回归曲线（→ `evals/run_eval_platform`）|
| 24 | `day24/day24_prompt_ab_judge.py` | prompt A/B + judge 一致性（独立可运行）|
| 25 | `day25/day25_agent_trajectory_eval.py` | Agent 轨迹评测（→ `evals/agent_trajectory_eval`）|
| 26 | `day26/day26_eval_report_failures.py` | 生产级失败诊断（DeepEval 维度分）+ 质量门禁（框架分判决 + 趋势守护）。原 day27 门禁已并入本天 |
| ~~27~~ | ~~`day27/day27_eval_dashboard.py`~~ | 已合并进 day26：诊断与门禁是同一动作的前后段，拆两天会误以为是两个并列能力；真正「接进 CI」的部署篇见 Day58（capstone/ci_gate.py + .github/workflows/eval-gate.yml）|

### 阶段3 Agent / LangGraph（Day28-40）

| Day | 文件 | 概念 |
|-----|------|------|
| 28 | `day28/day28_langgraph_basics.py` | LangGraph 入门：State / Node / Edge |
| 29 | `day29/day29_state_reducer.py` | 状态设计与 reducer |
| 30 | `day30/day30_react_agent.py` | ReAct |
| 31 | `day31/day31_node_reliability.py` | 节点容错与重试 |
| 32 | `day32/day32_structured_routing.py` | 结构化输出路由 |
| 33 | `day33/day33_plan_and_execute.py` | Plan-and-Execute |
| 34 | `day34/day34_observability.py` | 可观测性与调试 |
| 35 | `day35/day35_checkpoint_context.py` | 状态持久化 + 上下文管理 |
| 36 | `day36/day36_streaming_hitl.py` | streaming 中间步骤 + HITL |
| 37 | `day37/day37_tool_safety_search.py` | 工具安全 + 搜索 Agent（上）|
| 38 | `day38/day38_text2sql_agent.py` | Text2SQL 结构化数据问答工具 |
| 39 | `day39/day39_langgraph_supervisor.py` | Supervisor 多 Agent + Fan-out |
| 40 | `day40/day40_mcp_agent.py`（同目录含 server/debug 脚本） | MCP 接标准化工具 + A2A 了解 |

### 阶段4 工程化与可观测（Day41-48）

| Day | 文件 | 概念 |
|-----|------|------|
| 41 | `day41/day41_serve_fastapi.py` | FastAPI 服务化 |
| 42 | `day42/day42_reliability.py` | 异步 + 超时/重试/fallback |
| 43 | `day43/day43_cost_cache_routing.py` | 成本优化：缓存 + model routing |
| 44 | `day44/day44_sqlite_persistence.py` | 数据持久化：SQLite |
| 45 | `day45/day45_trace_docker.py` | trace + Docker 打包 |
| 46 | `day46/day46_ollama_inference.py` | 推理框架 Ollama（了解）|
| 47 | `day47/day47_security_guardrails.py` | 安全 guardrails：注入防护 + PII + 密钥 |
| 48 | `day48/day48_pytest_regression.py` | pytest 回归（接评测集）|

### 认知层（Day49-50，穿插，了解为主）

| Day | 文件 | 概念 |
|-----|------|------|
| 49 | `day49/day49_lora_finetune.py` | 微调取舍 + 跑一次 LoRA |
| 50 | `day50/day50_concept_overview.py` | 量化/蒸馏/Flash Attention/5 类输出 扫盲 |

### 阶段5：一个项目的完整开发过程（Day51-79）

> Day51 起连续开发同一个“企业客服与工单 Copilot”。每个 `dayNN/` 只保存当天新增或修改的完整文件；当天 README 同时记录项目完整结构，并标明新增、修改、继承但不涉及的文件。

| Day | 学习入口 | 当天真实交付 | 状态 |
|-----|----------|--------------|------|
| 51 | [`day51/README.md`](day51/README.md) | src 布局、本地 FAQ RAG、拒答、真实来源 | 完成 |
| 52–60 | [`Day52`](day52/README.md) → [`Day60`](day60/README.md) | 多文档、评测、混合检索、会话、LangGraph、订单、重试、人工、SQLite | 完成 |
| 61–69 | [`Day61`](day61/README.md) → [`Day69`](day69/README.md) | API、幂等、身份、增量同步、注入、PII、观测、缓存、质量门 | 完成 |
| 70–78 | [`Day70`](day70/README.md) → [`Day78`](day78/README.md) | 容器、存储迁移、容量、反馈、fallback、恢复、集成、面试证据、验收 | 完成 |
| 79 | [`day79/README.md`](day79/README.md) | 独立 Vite 前端、JWT 对接、聊天、来源、反馈和订单入口 | 完成 |

Day28–39 阶段分析文档归档在 [`day28-39/README.md`](day28-39/README.md)。

将数字替换成 51–78 中任意一天，即可还原该日结束时的完整项目：

```powershell
.\.venv\Scripts\python.exe tools\materialize_day.py 78
```

生成结果位于 `.build/day78/customer-support/`。每个 Day 只保存当日变更，完整结构和精确代码搜索目标记录在当天 README 中。

查看某一天相对上一天的真实文件变更：

```powershell
python tools/day_change_report.py 52
```

各日 README 记录了当天新增、修改和继承的文件；需要查看某日结束时的完整项目时，使用上面的还原命令即可。

### 浏览器演示入口

Day79 是独立的前端对接项目，代码位于 [`day79/`](day79/)。它通过 Vite 代理连接 Day78 的 FastAPI，页面可以演示多轮问答、JWT 身份、知识来源、订单查询和反馈闭环：

```bash
cd day79
npm install
npm run dev
```

前端地址是 <http://127.0.0.1:5173>；Day78 后端启动和 token 生成方式见 [`day79/README.md`](day79/README.md)。

### 阶段6：AI 自动化测试与质量工程（Day80–Day89）

| Day | 学习入口 | 主题 | 核心验收 |
|-----|----------|------|----------|
| 80 | [`day80/README.md`](day80/README.md) | AI 测试策略与风险建模 | 测试策略 + 风险矩阵 |
| 81 | [`day81/README.md`](day81/README.md) | 评估集与测试数据工程 | 版本化、分层测试集 |
| 82 | [`day82/README.md`](day82/README.md) | mock、契约与不变量测试 | 离线稳定自动化套件 |
| 83 | [`day83/README.md`](day83/README.md) | RAG 自动化测试 | 召回/生成/引用分层评测 |
| 84 | [`day84/README.md`](day84/README.md) | LLM-as-judge 校准 | 人工一致性与偏差报告 |
| 85 | [`day85/README.md`](day85/README.md) | Agent 自动化测试 | 真实工具轨迹与副作用测试 |
| 86 | [`day86/README.md`](day86/README.md) | AI API、流式与 E2E | SSE/鉴权/多租户端到端测试 |
| 87 | [`day87/README.md`](day87/README.md) | 安全、韧性与性能 | 对抗/故障注入/压测报告 |
| 88 | [`day88/README.md`](day88/README.md) | CI 分层门禁与防 flaky | PR/nightly/release 三层门禁 |
| 89 | [`day89/README.md`](day89/README.md) | 线上质量闭环（可选） | badcase 回流与量化改进复盘 |

这条 AI 测试专项线可以按天还原运行代码，例如：

```bash
python tools/materialize_ai_testing_day.py 89
cd .build/day89/ai-testing
pytest -q
```

`materialize_ai_testing_day.py` 会把 Day80 到指定 Day 的专项代码合并到 `.build/day<DAY>/ai-testing/`，用于验证每一天的增量结果。

这部分把测试背景转化为 AI 应用开发的差异化质量能力；时间紧时可优先完成 Day80–85，再按目标 JD 选学 API、安全、性能和线上质量。详细内容见 [`AI自动化测试专项学习大纲.md`](AI自动化测试专项学习大纲.md)。现有 Day18–26、Day48、Day58、Day62 已提供大部分前置基础。

### 阶段7–8：企业基础设施与多 Agent 协作（Day90–Day105）

Day90 起是独立的企业交付进阶工程，不会覆盖 Day51–79 的历史项目或本地 `customer_support/` 实验目录。它把已有的 RAG、评测、LangGraph 和 MCP 基础补成面向企业 AI 应用开发岗位的可测试能力：意图/槽位、PostgreSQL、Redis、Qdrant、Compose/Linux、vLLM，以及 MCP 鉴权与 A2A。

| Day | 主题 | 核心验收 |
|-----|------|----------|
| 90–93 | few-shot 意图、槽位追问、稳定 JSON、客服工作流 | 无法识别/缺参不执行副作用，状态可跨轮恢复 |
| 94–96 | PostgreSQL、Text2SQL 安全、Redis | RLS/参数化、执行计划门禁、缓存租户版本与限流 |
| 97–98 | pgvector/Qdrant/Milvus 选型、Compose/Linux | Qdrant tenant filter，Postgres+Redis+Qdrant 单机可复现 |
| 99–101 | OpenAI-compatible、vLLM、推理基准 | 模型配置、GPU 参数、质量+TTFT+p95 发布门禁 |
| 102–105 | MCP HTTP 鉴权、A2A 任务协议与集成 | scope/审批、Agent Card、JSON-RPC/SSE、客服委托订单 Agent |

完整路线和边界见 [`docs/day90-105_overview.md`](docs/day90-105_overview.md)。任意一天可独立还原：

```bash
python tools/materialize_enterprise_day.py 105
cd .build/day105/enterprise-support
python -m pytest -q
```

### 整合作品 `capstone/`（毕业项目主体）

多租户企业客服与工单 Copilot，端到端。详见 [`capstone/README.md`](capstone/README.md)。
核心模块：`knowledge_base.py`（混合检索+溯源）、`connector.py`（增量同步）、
`permissions.py`（文档级权限）、`auth.py`（JWT+多租户+限流）、`service.py`（统一编排）、
`approval.py`（持久化审批）、
`evaluation.py` + `ci_gate.py`（评测+门禁）、`monitoring.py`（监控）、
`api_enterprise.py`（唯一 HTTP 服务）、`test_production.py`（生产边界回归）。

## 辅助文件（非课程）

- `test_doc.txt` — RAG 用的测试文档

## 学习原则

- 一天只加一个新能力，每个新能力都踩在前一天的肩膀上。
- 重点不是"代码干净"，是"每行为什么这么写说得清"——说不清就是还没学透。
- 工程/界面（argparse、Streamlit 等）不抢核心概念的前排，放到项目环节再用。
