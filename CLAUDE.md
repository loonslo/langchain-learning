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
  prompt_ab_judge_agreement.py   #   Prompt A/B testing with judge consistency
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
python -m evals.prompt_ab_judge_agreement            # Prompt A/B testing
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
```

### Services
```bash
uvicorn day41_serve_fastapi:app --reload             # Day41 FastAPI service
uvicorn capstone.api:app --reload                    # Capstone API (http://127.0.0.1:8000/docs)
streamlit run capstone/app_streamlit.py              # Capstone Streamlit UI
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
