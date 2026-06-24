# 企业知识库 Agent + 自动化评测平台（毕业项目）

> 测试工程师转 AI 应用开发的整合作品。把 day01–66 学到的能力串成一个能跑、能测、能上线的项目。
> 差异化定位：不是又一个"聊天框 demo"，而是**带评测、可回归、可观测**的知识库 Agent——这正是测试背景的护城河。

## 能力一览

| 模块 | 文件 | 整合自 |
|------|------|--------|
| 文档处理 + 混合检索 + 溯源 | `knowledge_base.py` | day12–17 |
| 真实数据接入 + 增量同步 | `connector.py` | day54 |
| 文档级权限过滤（检索层） | `permissions.py` | day55 |
| 认证 + 多租户 + 限流 | `auth.py` | day56 |
| Agent 层（知识库工具 + HITL 审批） | `agent.py` | day28–36 |
| 自动化评测（指标 + 报告 + 失败库） | `evaluation.py` | day18–27 |
| CI 评测门禁 | `ci_gate.py` | day58 |
| 生产监控（p95/p99 + 成本） | `monitoring.py` | day62 |
| HTTP 服务（基础 / 企业版） | `api.py` / `api_enterprise.py` | day41/44/45/56 |
| pytest 回归 | `test_regression.py` | day48 |
| Web 界面（演示） | `app_streamlit.py` | — |
| CLI 入口 | `main.py` | — |

## 架构

```
                    ┌─────────────┐
   docs/(txt/md/pdf)│ knowledge_  │  混合检索(向量+BM25) + Chroma 持久化
        ─────────► │   base.py   │  带来源标注的问答链
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌────────────┐    ┌────────────┐
    │ agent.py │    │ api.py     │    │evaluation. │
    │ 工具+HITL│    │FastAPI+DB  │    │py 评测报告 │
    └──────────┘    └────────────┘    └────────────┘
                           ▲
                    test_regression.py（每次改动跑回归）
```

## 快速开始

```bash
# 1) 装依赖（见仓库根 README）+ 在根目录 .env 配 DEEPSEEK_API_KEY
pip install fastapi uvicorn pytest streamlit

# 2) 把你的文档放进 capstone/docs/（已带一个示例）

# 3) 建知识库
python capstone/main.py build

# 4) 提问
python capstone/main.py ask "RAG 为什么能减少幻觉？"

# 5) 跑评测出报告（data/eval_report.md + data/failures.json）
python capstone/main.py eval

# 6) 回归测试
pytest capstone/test_regression.py -v

# 7) 起服务 / 起界面
uvicorn capstone.api:app --reload          # http://127.0.0.1:8000/docs
streamlit run capstone/app_streamlit.py
```

## 工程化要点（面试可讲）

- **检索质量**：向量召回 + BM25 关键词召回融合，专有名词不漏；metadata 溯源，答案标来源。
- **质量护城河**：评测集 = 回归用例库；拒答正确率量化防幻觉；失败用例库归档错因（检索没召回 vs 召回了生成错）。
- **安全**：高风险动作（对外发布）走 human-in-the-loop 审批；密钥只走 `.env`，绝不进代码/仓库。
- **可观测**：每次问答落 SQLite，可统计；可叠加 LangSmith trace 定位失败步骤。
- **可复现**：被测链 `temperature=0`，回归断言用"含关键词/是否拒答"宽松匹配，避开随机性。
