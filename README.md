# LangChain 学习记录 · 测试工程师转 AI 应用开发

> 循序渐进的每日代码：从"问一次"到"能查文档、能评测、能上线"，一天一个核心概念。
> 每个文件开头有「这天学什么」，关键行有注释，能独立运行。
> 2026-06-23 起按新版 `AI应用开发-完整学习大纲.md` / `AI应用开发-每日任务清单.md`
> 对齐：新版计划是 Day1-71，旧代码的 Day10 以后存在编号错位。本 README 先保留旧代码索引，
> 并在下面列出新版补齐文件和映射，后续可以再做批量重命名。

## 新版方案对齐状态（Day1-44）

结论：Day1-9 已基本和新版一致；Day10 以后原仓库是旧编号，已通过新增文件和模块补齐关键缺口。

| 新版范围 | 当前状态 | 对应文件 / 模块 |
|---|---|---|
| Day1-Day9 | 已对齐 | `day01_first_chat.py` 到 `day09_minimal_rag.py` |
| Day10 裸 SDK RAG + agent loop | 已补齐 | `day10_raw_sdk_rag_agent_loop.py` |
| Day11 LLM 原理 | 旧编号可复用 | `day10_llm_principles.py` |
| Day12-Day17 RAG 进阶 | 旧编号整体前移，可复用 | `day11_rag_pdf_sources.py` 到 `day16_rag_multimodal_rerank.py` |
| Day18-Day27 双评测平台 | 已补关键证据链 | `day17-day22` + `evals/` + `reports/` |
| Day28-Day40 Agent / LangGraph | 旧编号可复用，Text2SQL 已补 | `day23-day34`、`day31_mcp_*`、`day38_text2sql_agent.py` |
| Day41-Day44 工程化 | 旧编号可复用 | `day35_serve_fastapi.py` 到 `day38_sqlite_persistence.py` |

### 阶段2评测平台（新版 Day18-Day27）

新增 `evals/` 作为可单独展示的评测模块，覆盖新版任务清单要求的 50+ 评测集、回归记录、
Prompt A/B、judge 一致性、Agent 轨迹评测、失败用例库、成本/延迟基线和 HTML 看板。

```bash
python -m evals.run_eval_platform
python -m evals.prompt_ab_judge_agreement
python -m evals.agent_trajectory_eval
python -m evals.dashboard
```

生成物在 `reports/`：

- `eval_runs.csv`：每次评测的 commit、通过率、延迟、token、成本、失败数。
- `latest_report.md`：最近一次质量评测摘要。
- `failures.json`：失败用例库。
- `prompt_ab_judge_agreement.json`：Prompt A/B 与 judge 一致性结果。
- `agent_trajectory_eval.json`：Agent 工具轨迹评测结果。
- `dashboard.html`：可展示评测看板。

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

工程化阶段（Day35+）还需要：`pip install fastapi uvicorn pytest`

## 课程地图

### ✅ 基础 → 最小 RAG（Day1–9，已学）

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
| 9 | `day09_minimal_rag.py` | 最小 RAG：完整问答（MMR、拒答） |

### 固本收尾（Day10）

| Day | 文件 | 概念 |
|-----|------|------|
| 10 | `day10_llm_principles.py` | LLM 原理认知（token/embedding/attention/幻觉） |

### RAG 进阶（Day11–16）

| Day | 文件 | 概念 |
|-----|------|------|
| 11 | `day11_rag_pdf_sources.py` | 处理真实文档（PDF）+ 来源溯源 + 封装 |
| 12 | `day12_rag_chunk_strategy.py` | chunk 策略对比 |
| 13 | `day13_rag_hybrid_search.py` | 混合检索：向量 + BM25 |
| 14 | `day14_rag_query_rewrite.py` | 查询改写：Multi-Query + HyDE |
| 15 | `day15_rag_chroma_persist.py` | 向量库持久化：Chroma |
| 16 | `day16_rag_multimodal_rerank.py` | 多模态 + reranker |

### RAG 评测 ★护城河（Day17–22）

| Day | 文件 | 概念 |
|-----|------|------|
| 17 | `day17_rag_eval_basics.py` | 造评测集 + 手写三大指标 |
| 18 | `day18_rag_eval_llm_judge.py` | LLM-as-judge：正确性/忠实度 |
| 19 | `day19_eval_dataset_build.py` | 造评测集（上）：schema + 事实/跨段落 |
| 20 | `day20_eval_dataset_ragas.py` | 造评测集（下）：拒答/引用 + RAGAS |
| 21 | `day21_langsmith_eval.py` | LangSmith trace + 在线评估 |
| 22 | `day22_rag_eval_report.py` | 评测报告 + 失败用例库 |

### Agent / LangGraph（Day23–34）

| Day | 文件 | 概念 |
|-----|------|------|
| 23 | `day23_langgraph_basics.py` | LangGraph 入门：State / Node / Edge |
| 24 | `day24_langgraph_branch_loop.py` | 条件分支 + 循环 + recursion_limit 防死循环 |
| 25 | `day25_langgraph_tool_agent.py` | 用图重写工具调用（对比 day05 手写循环）|
| 26 | `day26_react_agent.py` | ReAct：create_react_agent + 规划范式速览 |
| 27 | `day27_plan_and_execute.py` | Plan-and-Execute：先规划再执行 |
| 28 | `day28_checkpoint_persistence.py` | checkpoint 持久化 + 多轮记忆 |
| 29 | `day29_context_and_streaming.py` | 上下文裁剪/摘要 + streaming |
| 30 | `day30_human_in_the_loop.py` | HITL：interrupt 人工审批 + 工具安全 |
| 31 | `day31_mcp_agent.py` (+ `day31_mcp_server.py`) | MCP：标准协议给 Agent 接工具 |
| 32 | `day32_multi_agent.py` | 多 Agent 编排：supervisor 路由（AutoGen/CrewAI/A2A 了解）|
| 33 | `day33_search_agent.py` | 项目（上）：搜索+总结 Agent + ReAct + 轨迹日志 |
| 34 | `day34_search_agent_hitl.py` | 项目（下）：加 HITL + checkpoint 端到端 |

### 工程化（Day35–42）

| Day | 文件 | 概念 |
|-----|------|------|
| 35 | `day35_serve_fastapi.py` | FastAPI 把 RAG 包成 HTTP 接口 |
| 36 | `day36_reliability.py` | 超时 + 重试 + token/成本统计 |
| 37 | `day37_cost_cache_routing.py` | 成本优化：缓存 + model routing |
| 38 | `day38_sqlite_persistence.py` | 数据持久化：SQLite 存对话/用户 |
| 39 | `day39_observability_ollama.py` | 可观测：结构化日志 + Ollama 本地推理（了解）|
| 40 | `day40_deploy_docker.py` | Docker 打包部署（生成 Dockerfile 示例）|
| 41 | `day41_security_guardrails.py` | 注入防护 + PII 脱敏 + 密钥管理 |
| 42 | `day42_pytest_regression.py` | pytest 自动化回归 |

### 认知层（Day43–44）

| Day | 文件 | 概念 |
|-----|------|------|
| 43 | `day43_rag_prompt_finetune.py` | RAG / Prompt / 微调 选型 + 5 类输出方式 |
| 44 | `day44_lora_finetune.py` | LoRA 最小脚本 + 量化/蒸馏/Scaling Laws 扫盲 |

### 毕业项目 + 求职（Day45–54）

整合作品在 `capstone/` 目录：企业知识库 Agent + 自动化评测平台，端到端。

| 内容 | 文件 |
|------|------|
| 项目说明 + 架构 + 运行 | `capstone/README.md` |
| 文档处理 + 混合检索 + 溯源 | `capstone/knowledge_base.py` |
| Agent 层（工具 + HITL 审批） | `capstone/agent.py` |
| 自动化评测（指标/报告/失败库） | `capstone/evaluation.py` |
| FastAPI 服务 + SQLite 落库 | `capstone/api.py` |
| pytest 回归 | `capstone/test_regression.py` |
| Web 界面 / CLI 入口 | `capstone/app_streamlit.py` / `capstone/main.py` |
| 简历项目描述 | `capstone/简历项目描述.md` |
| 面试题准备 | `capstone/面试题准备.md` |

> 至此 day01–44 + capstone 全部完成，覆盖大纲 M1–M9 与阶段 0–5。

## 辅助文件（非课程）

- `tess.py` — 一次性脚本：下载 embedding 模型
- `test_doc.txt` — RAG 用的测试文档

## 学习原则

- 一天只加一个新能力，每个新能力都踩在前一天的肩膀上。
- 重点不是"代码干净"，是"每行为什么这么写说得清"——说不清就是还没学透。
- 工程/界面（argparse、Streamlit 等）不抢核心概念的前排，放到项目环节再用。
