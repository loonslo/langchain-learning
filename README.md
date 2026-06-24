# LangChain 学习记录 · 测试工程师转 AI 应用开发

> 循序渐进的每日代码：从"问一次"到"能查文档、能评测、能上线"，一天一个核心概念。
> 每个文件开头有「这天学什么」，关键行有注释，能独立运行。
> 严格对齐 `AI应用开发-完整学习大纲.md` / `AI应用开发-每日任务清单.md`：**统一编号 Day1-71，文件名即 dayNN**。
> 2026-06-24 完成全量重排：旧版错位编号已删除，现一套干净的 day01-71。

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

## 课程地图（Day1-71，文件名即 dayNN）

> 阶段5-7 的整合单元是 `dayNN` 驱动文件，复用 `capstone/` + `evals/` 模块（不重复造）。
> 求职天（Day67-71）是 `dayNN_*.md`。

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
| 24 | `day24_prompt_ab_judge.py` | prompt A/B + judge 一致性（→ `evals/prompt_ab_judge_agreement`）|
| 25 | `day25_agent_trajectory_eval.py` | Agent 轨迹评测（→ `evals/agent_trajectory_eval`）|
| 26 | `day26_eval_report_failures.py` | 评测报告 + 失败用例库 + 成本/延迟基线 |
| 27 | `day27_eval_dashboard.py` | 评测看板（→ `evals/dashboard`，首个可投作品）|

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

### 阶段5 毕业项目整合 + 企业第一梯队 + 真上线（Day51-61）

> 代码主体在 `capstone/`，每个 dayNN 是"这天做哪块"的驱动/说明。

| Day | 文件 | 概念 |
|-----|------|------|
| 51 | `day51_project_skeleton.py` | 项目架构 + Git 协作工作流 |
| 52 | `day52_capstone_rag_eval.py` | RAG + Chroma + 评测接入（真实语料）|
| 53 | `day53_capstone_agent.py` | Agent + MCP + HITL + agent 评测接入 |
| 54 | `day54_incremental_sync.py` | 真实数据接入 + 增量同步（→ `capstone/connector.py`）|
| 55 | `day55_doc_permissions.py` | 文档级权限过滤·检索层（→ `capstone/permissions.py`）|
| 56 | `day56_auth_multitenant.py` | 认证 + 多租户 + 限流（→ `capstone/auth.py` / `api_enterprise.py`）|
| 57 | `day57_engineering_integration.py` | 工程化接入清单 |
| 58 | `day58_ci_gate.py` ★ | CI 评测门禁（→ `capstone/ci_gate.py` + `.github/workflows/eval-gate.yml`）|
| 59 | `day59_e2e_improvement_loop.py` | 端到端联调 + 一轮改进闭环 |
| 60 | `day60_deploy.py` | 真部署拿公网地址（详见 `capstone/DEPLOY.md`）|
| 61 | `day61_github_polish.py` | GitHub 打磨清单 |

### 阶段6 上线补全（Day62-66）

| Day | 文件 | 概念 |
|-----|------|------|
| 62 | `day62_monitoring_alerting.py` | 生产监控 p95/p99 + 告警（+ `capstone/monitoring.py`）|
| 63 | `day63_pgvector_store.py` | 生产级向量库 pgvector |
| 64 | `day64_content_safety.py` | 内容安全 / 合规审核 |
| 65 | `day65_provider_abstraction.py` | 模型供应商抽象（OpenAI/Azure/Bedrock）|
| 66 | `day66_loadtest_locust.py` | locust 压测 + OpenAPI /v1 |

### 阶段7 求职冲刺（Day67-71，markdown）

| Day | 文件 | 概念 |
|-----|------|------|
| 67 | `day67_resume.md` | 简历 + 求职定位 |
| 68 | `day68_interview_rag_agent.md` | 面试题：RAG / Agent / 评测 |
| 69 | `day69_interview_enterprise.md` | 面试题：工程 / 企业 / 上线 |
| 70 | `day70_project_pitch.md` | 5 分钟项目讲解 |
| 71 | `day71_mock_interview.md` | 模拟面试 + 复盘 |

### 整合作品 `capstone/`（毕业项目主体）

企业知识库 Agent + 自动化评测平台，端到端。详见 `capstone/README.md`。
核心模块：`knowledge_base.py`（混合检索+溯源）、`connector.py`（增量同步）、
`permissions.py`（文档级权限）、`auth.py`（JWT+多租户+限流）、`agent.py`（Agent+HITL）、
`evaluation.py` + `ci_gate.py`（评测+门禁）、`monitoring.py`（监控）、
`api.py` / `api_enterprise.py`（服务）、`test_regression.py`（回归）。

### 评测平台 `evals/`（阶段2 可单独展示）

```bash
python -m evals.run_eval_platform        # 质量+成本+延迟+失败库+回归记录
python -m evals.prompt_ab_judge_agreement # prompt A/B + judge 一致性
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
