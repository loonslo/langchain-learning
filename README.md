# LangChain 学习记录 · 测试工程师转 AI 应用开发

> 循序渐进的每日代码：从"问一次"到"能查文档、能评测、能上线"，一天一个核心概念。
> 每个文件开头有「这天学什么」，关键行有注释，能独立运行。
> 核心课程 Day1–50 建立 AI 应用开发与评测底座；Day51–78 连续开发一个生产导向项目。Day79–88 是可选的 AI 自动化测试 backup 路线。

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

## 课程地图（Day1-78）

> Day1–50 使用独立练习文件建立基础；Day51–78 使用“每日完整变更集”推进同一个项目。每天除了新增文件，还必须展示被改写的旧文件和继续参与主链但未改的文件。README 记录当天完整结构，未修改文件不重复复制，并可用 `tools/materialize_day.py` 还原任意一天。

### 阶段0 固本 + 裸写 harness（Day1-11）

| Day | 文件 | 概念 |
|-----|------|------|
| 1 | `day01_first_chat.py` | 基础调用 + Prompt + LCEL 管道 |
| 2 | `day02_control_output.py` | 控制输出：temperature + 流式 |
| 3 | `day03_structured_output.py` | 结构化输出：Pydantic |
| 4 | `day04_memory_chat.py` | 多轮记忆 |
| 5 | `day05_tool_calling.py` | 工具调用 |
| 6 | `day06_chatbot_project.py` | 综合项目：记忆+工具+多角色 |
| 7 | `day07_rag_load_split.py` | RAG：加载 + 切割 |
| 8 | `day08_rag_embed_retrieve.py` | RAG：向量化 + 检索 |
| 9 | `day09_minimal_rag.py` | 最小 RAG：完整问答（MMR、拒答）+ 提示工程 |
| 10 | `day10_raw_sdk_rag_agent_loop.py` | 裸 SDK 手写 RAG + agent loop（理解 harness）|
| 11 | `day11_llm_principles.py` | LLM 原理认知（token/embedding/attention/幻觉）|

### 阶段1 RAG 进阶（Day12-17）

| Day | 文件 | 概念 |
|-----|------|------|
| 12 | `day12_rag_pdf_sources.py` | 处理真实 PDF + 来源溯源 + 封装 |
| 13 | `day13_rag_chunk_strategy.py` | chunk 策略对比 |
| 14 | `day14_rag_hybrid_search.py` | 混合检索：向量 + BM25 |
| 15 | `day15_rag_query_rewrite.py` | 查询改写：Multi-Query + HyDE + Context Engineering |
| 16 | `day16_rag_chroma_persist.py` | 向量库持久化：Chroma |
| 17 | `day17_rag_multimodal_rerank.py` | 多模态读图 + reranker |

### 阶段2 RAG + Agent 双评测 ★护城河（Day18-27）

| Day | 文件 | 概念 |
|-----|------|------|
| 18 | `day18_eval_basics.py` | 评测集 + 手写三大指标 |
| 19 | `day19_eval_llm_judge.py` | LLM-as-judge：正确性/忠实度 |
| 20 | `day20_eval_dataset_build.py` | 造评测集（上）：schema + 事实/跨段落 |
| 21 | `day21_eval_dataset_ragas.py` | 造评测集（下）：拒答/引用 + RAGAS/DeepEval |
| 22 | `day22_langsmith_eval.py` | LangSmith trace + 在线评估 |
| 23 | `day23_eval_regression_curve.py` | 评测集版本化 + 回归曲线（→ `evals/run_eval_platform`）|
| 24 | `day24_prompt_ab_judge.py` | prompt A/B + judge 一致性（独立可运行）|
| 25 | `day25_agent_trajectory_eval.py` | Agent 轨迹评测（→ `evals/agent_trajectory_eval`）|
| 26 | `day26_eval_report_failures.py` | 生产级失败诊断（DeepEval 维度分）+ 质量门禁（框架分判决 + 趋势守护）。原 day27 门禁已并入本天 |
| ~~27~~ | ~~`day27_eval_dashboard.py`~~ | 已合并进 day26：诊断与门禁是同一动作的前后段，拆两天会误以为是两个并列能力；真正「接进 CI」的部署篇见 Day58（capstone/ci_gate.py + .github/workflows/eval-gate.yml）|

### 阶段3 Agent / LangGraph（Day28-40）

| Day | 文件 | 概念 |
|-----|------|------|
| 28 | `day28_langgraph_basics.py` | LangGraph 入门：State / Node / Edge |
| 29 | `day29_langgraph_branch_loop.py` | 条件分支 + 循环 + recursion_limit |
| 30 | `day30_langgraph_tool_agent.py` | 用图重写工具调用（上）|
| 31 | `day31_langgraph_vs_manual.py` | 重写完成 + 对比手写循环（harness）|
| 32 | `day32_react_agent.py` | ReAct |
| 33 | `day33_plan_and_execute.py` | Plan-and-Execute |
| 34 | `day34_planning_paradigms.py` | 其他规划范式 + AutoGen/CrewAI/A2A（了解）|
| 35 | `day35_checkpoint_context.py` | 状态持久化 + 上下文管理 |
| 36 | `day36_streaming_hitl.py` | streaming 中间步骤 + HITL |
| 37 | `day37_tool_safety_search.py` | 工具安全 + 搜索 Agent（上）|
| 38 | `day38_text2sql_agent.py` | Text2SQL 结构化数据问答工具 |
| 39 | `day39_search_agent_eval.py` | 搜索+总结 Agent 完成 + 接轨迹评测 |
| 40 | `day40_mcp_agent.py` (+ `day40_mcp_server.py`) | MCP 接标准化工具 + A2A 了解 |

### 阶段4 工程化与可观测（Day41-48）

| Day | 文件 | 概念 |
|-----|------|------|
| 41 | `day41_serve_fastapi.py` | FastAPI 服务化 |
| 42 | `day42_reliability.py` | 异步 + 超时/重试/fallback |
| 43 | `day43_cost_cache_routing.py` | 成本优化：缓存 + model routing |
| 44 | `day44_sqlite_persistence.py` | 数据持久化：SQLite |
| 45 | `day45_trace_docker.py` | trace + Docker 打包 |
| 46 | `day46_ollama_inference.py` | 推理框架 Ollama（了解）|
| 47 | `day47_security_guardrails.py` | 安全 guardrails：注入防护 + PII + 密钥 |
| 48 | `day48_pytest_regression.py` | pytest 回归（接评测集）|

### 认知层（Day49-50，穿插，了解为主）

| Day | 文件 | 概念 |
|-----|------|------|
| 49 | `day49_lora_finetune.py` | 微调取舍 + 跑一次 LoRA |
| 50 | `day50_concept_overview.py` | 量化/蒸馏/Flash Attention/5 类输出 扫盲 |

### 阶段5：一个项目的完整开发过程（Day51-78）

> Day51 起连续开发同一个“企业客服与工单 Copilot”。每个 `dayNN/` 只保存当天新增或修改的完整文件；当天 README 同时记录项目完整结构，并标明新增、修改、继承但不涉及的文件。

| Day | 学习入口 | 当天真实交付 | 状态 |
|-----|----------|--------------|------|
| 51 | [`day51/README.md`](day51/README.md) | src 布局、本地 FAQ RAG、拒答、真实来源 | 完成 |
| 52–60 | [`Day52`](day52/README.md) → [`Day60`](day60/README.md) | 多文档、评测、混合检索、会话、LangGraph、订单、重试、人工、SQLite | 完成 |
| 61–69 | [`Day61`](day61/README.md) → [`Day69`](day69/README.md) | API、幂等、身份、增量同步、注入、PII、观测、缓存、质量门 | 完成 |
| 70–78 | [`Day70`](day70/README.md) → [`Day78`](day78/README.md) | 容器、存储迁移、容量、反馈、fallback、恢复、集成、面试证据、验收 | 完成 |

将数字替换成 51–78 中任意一天，即可还原该日结束时的完整项目：

```powershell
.\.venv\Scripts\python.exe tools\materialize_day.py 78
```

生成结果位于 `.build/day78/customer-support/`。每个 Day 只保存当日变更，完整结构和精确代码搜索目标记录在当天 README 中。

查看某一天相对上一天的真实文件变更：

```powershell
python tools/day_change_report.py 52
```

Day51–Day54 的逐文件衔接说明见 [`docs/Day51-Day54衔接变更总览.md`](docs/Day51-Day54衔接变更总览.md)；后续完整主线见 [`docs/Day55-Day78衔接总览.md`](docs/Day55-Day78衔接总览.md)。

### 可选补充：AI 自动化测试 backup（Day79-88，规划中）

| Day | 主题 | 核心验收 |
|-----|------|----------|
| 79 | AI 测试策略与风险建模 | 测试策略 + 风险矩阵 |
| 80 | 评估集与测试数据工程 | 版本化、分层测试集 |
| 81 | mock、契约与不变量测试 | 离线稳定自动化套件 |
| 82 | RAG 自动化测试 | 召回/生成/引用分层评测 |
| 83 | LLM-as-judge 校准 | 人工一致性与偏差报告 |
| 84 | Agent 自动化测试 | 真实工具轨迹与副作用测试 |
| 85 | AI API、流式与 E2E | SSE/鉴权/多租户端到端测试 |
| 86 | 安全、韧性与性能 | 对抗/故障注入/压测报告 |
| 87 | CI 分层门禁与防 flaky | PR/nightly/release 三层门禁 |
| 88 | 线上质量闭环（可选） | badcase 回流与量化改进复盘 |

这部分只在准备 AI 自动化测试岗位时选学，不阻塞 AI 应用开发主线和求职进度。详细内容见 [`AI自动化测试专项学习大纲.md`](AI自动化测试专项学习大纲.md)。现有 Day18-26、Day48、Day58、Day62 已提供大部分前置基础。

### 整合作品 `capstone/`（毕业项目主体）

多租户企业客服与工单 Copilot，端到端。详见 `capstone/README.md`。
核心模块：`knowledge_base.py`（混合检索+溯源）、`connector.py`（增量同步）、
`permissions.py`（文档级权限）、`auth.py`（JWT+多租户+限流）、`service.py`（统一编排）、
`approval.py`（持久化审批）、
`evaluation.py` + `ci_gate.py`（评测+门禁）、`monitoring.py`（监控）、
`api_enterprise.py`（唯一 HTTP 服务）、`test_production.py`（生产边界回归）。

### 评测平台 `evals/`（阶段2 可单独展示）

```bash
python -m evals.run_eval_platform        # 质量+成本+延迟+失败库+回归记录
python day24_prompt_ab_judge.py          # prompt A/B + judge 一致性
python -m evals.agent_trajectory_eval     # Agent 轨迹评测
python -m evals.dashboard                 # 生成 reports/dashboard.html 看板
```

生成物在 `reports/`：`eval_runs.csv`（回归曲线原料）、`latest_report.md`、`failures.json`、
`prompt_ab_judge_agreement.json`、`agent_trajectory_eval.json`、`dashboard.html`。

## 辅助文件（非课程）

- `tess.py` — 一次性脚本：下载 embedding 模型
- `test_doc.txt` — RAG 用的测试文档

## 学习原则

- 一天只加一个新能力，每个新能力都踩在前一天的肩膀上。
- 重点不是"代码干净"，是"每行为什么这么写说得清"——说不清就是还没学透。
- 工程/界面（argparse、Streamlit 等）不抢核心概念的前排，放到项目环节再用。
