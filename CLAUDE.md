# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Chinese-language LangChain learning curriculum (Day1-71) for a test engineer transitioning to AI application development. Covers RAG, evaluation (护城河 speciality), LangGraph agents, engineering/deployment, and enterprise features. The capstone project is an enterprise knowledge base agent + automated evaluation platform.

## Architecture

```
common.py                        # Shared backbone: LLM factory (DeepSeek), embedding cache, Chinese separators
dayNN_*.py                       # 71 self-contained daily learning files, each importable from common.py
capstone/                        # Graduation project: enterprise knowledge base + eval platform
  config.py                      #   Imports common.py, adds project paths (DOCS_DIR, CHROMA_DIR, DB_PATH etc.)
  knowledge_base.py              #   Hybrid retrieval (vector + BM25) + Chroma persistence + source citation
  agent.py                       #   Tool-calling agent with HITL approval
  evaluation.py / ci_gate.py     #   Automated eval metrics, report generation, CI quality gate
  test_regression.py             #   pytest regression tests (the key differentiator)
  api.py / api_enterprise.py     #   FastAPI service / enterprise version with auth + multi-tenant
  auth.py / permissions.py       #   JWT auth, document-level permissions, rate limiting
  monitoring.py / connector.py   #   Production monitoring (p95/p99), data ingestion + incremental sync
  main.py                        #   CLI entry point (build / ask / eval)
evals/                           # Standalone evaluation platform module
  run_eval_platform.py           #   Quality + cost + latency + failure analysis + regression history
  dashboard.py                   #   Generates reports/dashboard.html
  prompt_ab_judge_agreement.py   #   Compatibility entry; Day24 implementation lives in day24_prompt_ab_judge.py
  agent_trajectory_eval.py       #   Agent trajectory evaluation
reports/                         # Generated outputs: eval_runs.csv, failures.json, latest_report.md, dashboard.html
```

## Key Commands

### Daily learning files
```bash
python dayNN_filename.py         # Run any day's file directly
```

### Evaluation platform (offline by default, no API key needed)
```bash
python -m evals.run_eval_platform                    # Offline mode (demo answers)
python -m evals.run_eval_platform --mode live        # Live mode (requires DEEPSEEK_API_KEY)
python -m evals.dashboard                            # Generate HTML dashboard
python day24_prompt_ab_judge.py                      # Prompt A/B testing
python -m evals.agent_trajectory_eval                # Agent trajectory evaluation
```

### Capstone project
```bash
python capstone/main.py build                        # Build knowledge base from docs/
python capstone/main.py ask "your question"          # Ask the knowledge base
python capstone/main.py eval                         # Run evaluation + report
```

### Testing (pytest is the primary test framework)
```bash
pytest day48_pytest_regression.py -v                 # RAG regression tests
pytest capstone/test_regression.py -v                # Capstone regression tests
pytest test_day47.py -v                              # Security guardrails (injection detection, PII masking, secret scrubbing)
pytest test_day44.py -v                              # SQLite data layer (injection, WAL concurrency, migration)
pytest test_day41.py -v                              # FastAPI service (fake RAG, no LLM/API key needed)
```

### Load testing (SLO gate, exit code 1 on violation)
```bash
python day66_loadtest_locust.py --fake --users 20 --time 30s --upstream-ms 800   # fake upstream, no API cost, CI-safe
python day66_loadtest_locust.py --host http://127.0.0.1:8000 --users 10 --time 60s  # against real service
locust -f day66_loadtest_locust.py --host http://127.0.0.1:8000                   # interactive UI
```

### LoRA fine-tuning (regression gate, exit code 1 if adapter is not better than base)
```bash
python day49_lora_finetune.py --smoke                                   # tiny model, CPU seconds, flow only, no quality assertion
python day49_lora_finetune.py                                           # Qwen2.5-0.5B-Instruct, ~4min on CPU; base-vs-adapter gate
python day49_lora_finetune.py --base <path-or-repo> --epochs 20         # HF_ENDPOINT=https://hf-mirror.com if HF is unreachable
python day49_lora_finetune.py --export-llamafactory                     # emit equivalent LLaMA-Factory dataset + YAML (no training)
```

### Services
```bash
uvicorn day41_serve_fastapi:app --reload             # Day41 FastAPI service
uvicorn capstone.api:app --reload                    # Capstone API (http://127.0.0.1:8000/docs)
streamlit run capstone/app_streamlit.py              # Capstone Streamlit UI
python day40_mcp_server_http.py                      # Day40 remote MCP server (streamable-http, :8000/mcp)
```

### Docker
```bash
docker build -f Dockerfile.example -t langchain-app .
```

### CI
```bash
# GitHub Actions workflow at .github/workflows/eval-gate.yml
# Runs: pytest capstone/test_regression.py + python capstone/ci_gate.py
```

## Environment & Dependencies

- **LLM**: DeepSeek via OpenAI-compatible API (`DEEPSEEK_API_KEY` in `.env`)
- **Embedding**: Local BGE models (bge-small-zh-v1.5, bge-reranker-base) downloaded via ModelScope
- **Python**: 3.11
- **Key packages**: langchain, langchain-openai, langchain-community, langchain-huggingface, langchain-chroma, langgraph, faiss-cpu, rank_bm25, pypdf
- **`.env` config**: `DEEPSEEK_API_KEY`, optional `LANGSMITH_API_KEY`, `EMBED_MODEL_PATH`, `RERANKER_MODEL_PATH`
- **No build system** (no pyproject.toml/setup.py) — just Python files with pip dependencies

## Testing Patterns

- RAG tests use **loose assertions** (keyword matching, refusal detection) instead of exact string matching
- `temperature=0` in LLM factory for reproducibility
- Capstone eval uses a JSON eval set with quantifyable metrics (keyword score ≥ 0.67, citation score ≥ 0.67)
- CI gate blocks merge if quality drops below threshold

# Memory

Working memory for the productivity system. Full knowledge base in `memory/`.

## Me
ajar（loonslo），测试工程师，正在转 AI Agent 应用开发。目标：2~3 个月内完成学习并跳槽（起点约 2026-07）。

## Terms
| 术语 | 含义 |
|------|------|
| 护城河 | 评估 + 测试背景：pytest 回归、CI 质量门禁、评估平台 |
| capstone | 毕业项目：企业知识库 Agent + 自动化评估平台 |
| 转行日记 | 小红书每日学习帖（ai-transition-diary 技能生成） |

## Projects
| 名称 | 内容 |
|------|------|
| **langchain-learning** | 主项目：Day1-71 学习曲线 + capstone，详见 memory/projects/ |

## Preferences
- 中文交流，简洁直接
- 只保留高效、以转行为第一性目标的代码与任务
- 任务记录在 TASKS.md，用 dashboard.html 可视化管理
