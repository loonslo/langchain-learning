# LangChain 学习记录 · 测试工程师转 AI 应用开发

> 循序渐进的每日代码：从"问一次"到"能查文档、能评测、能上线"，一天一个核心概念。
> 每个文件开头有「这天学什么」，关键行有注释，能独立运行。
> 编号与学习计划（任务清单 / 大纲）统一：同一个 Day 号两边指同一件事。
> 跳号（如 Day12、Day16、Day23–34…）是还没写的内容，先占位，后面按节奏补。

## 环境

```bash
pip install langchain langchain-openai langchain-community python-dotenv \
            langchain-text-splitters faiss-cpu pypdf langchain-huggingface \
            langchain-chroma rank_bm25
```

`.env` 配置（用 DeepSeek，兼容 OpenAI 格式）：

```
DEEPSEEK_API_KEY=你的key
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
| 12 | _(待写)_ | chunk 策略对比 |
| 13 | `day13_rag_hybrid_search.py` | 混合检索：向量 + BM25 |
| 14 | `day14_rag_query_rewrite.py` | 查询改写：Multi-Query + HyDE |
| 15 | `day15_rag_chroma_persist.py` | 向量库持久化：Chroma |
| 16 | _(待写)_ | 多模态 + reranker |

### RAG 评测 ★护城河（Day17–22）

| Day | 文件 | 概念 |
|-----|------|------|
| 17 | `day17_rag_eval_basics.py` | 造评测集 + 手写三大指标 |
| 18 | `day18_rag_eval_llm_judge.py` | LLM-as-judge：正确性/忠实度 |
| 19–21 | _(待写)_ | 造评测集（扩充）/ RAGAS / LangSmith |
| 22 | `day22_rag_eval_report.py` | 评测报告 + 失败用例库 |

### Agent / LangGraph（Day23–34，待写）

LangGraph 入门 / 条件分支循环 / ReAct / Plan-and-Execute / 状态持久化 / HITL / MCP

### 工程化（Day35–42）

| Day | 文件 | 概念 |
|-----|------|------|
| 35 | `day35_serve_fastapi.py` | FastAPI 把 RAG 包成 HTTP 接口 |
| 36 | `day36_reliability.py` | 超时 + 重试 + token/成本统计 |
| 37–40 | _(待写)_ | 成本/缓存/路由 / SQLite / trace + Docker |
| 41 | `day41_security_guardrails.py` | 注入防护 + PII 脱敏 + 密钥管理 |
| 42 | `day42_pytest_regression.py` | pytest 自动化回归 |

### 认知层（Day43–44，待写）

微调取舍 / 量化蒸馏等概念扫盲（了解为主）

### 毕业项目 + 求职（Day45–54，待写）

企业知识库 Agent + 自动化评测平台，端到端整合 + GitHub + 简历 + 面试

## 辅助文件（非课程）

- `tess.py` — 一次性脚本：下载 embedding 模型
- `test_doc.txt` — RAG 用的测试文档

## 学习原则

- 一天只加一个新能力，每个新能力都踩在前一天的肩膀上。
- 重点不是"代码干净"，是"每行为什么这么写说得清"——说不清就是还没学透。
- 工程/界面（argparse、Streamlit 等）不抢核心概念的前排，放到项目环节再用。
