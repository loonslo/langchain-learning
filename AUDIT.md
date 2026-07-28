# Day1-78 第一性审计报告（2026-07-20）

评审基准：2026 企业用工需求（英文数据源核实）——Python、RAG+混合检索+重排、向量库、
Agent 编排+MCP、**评估能力（招聘方眼中"真做过 LLM 应用"的最强信号）**、护栏、
LLMOps（trace/成本/延迟/prompt 版本化）、部署；微调为加分项（薪资 +10~15%）。

**总结论：76 个文件全部保留，无低效模块。** 课程主题与企业需求逐项对得上，
护城河定位（评估+测试）恰好压在招聘方最看重的信号上。问题集中在三类，已全部修复。

## 逐日结论

| Day | 主题 | 结论 |
|-----|------|------|
| 1-6 | 基础：调用/输出控制/结构化/记忆/工具/小项目 | ✅ 合理。day04 已注明 RunnableWithMessageHistory 弃用警告 |
| 7-9 | RAG 建库三步 | ✅ 合理。day07/09 已避开 community TextLoader；**day08 补 community 归档注释** |
| 10 | 裸 SDK 手写 RAG+agent loop | ✅ 保留。理解 harness，面试差异化 |
| 11 | LLM 原理认知 | ✅ 合理，定位【了解】级正确 |
| 12-17 | RAG 进阶：PDF/chunk/混合/改写/持久化/重排 | ✅ 合理，混合检索+重排正是 2026 JD 高频。**day14 修 BM25 中文分词失效 bug + 补 community 归档注释** |
| 18-26 | 评估九连（护城河） | ✅ 核心资产，占比合理。**day18-22 修引用漂移共 24 处**（评测集编号整体错位 1） |
| 27-39 | LangGraph Agent 段 | ✅ 合理，覆盖 state/reducer/容错/路由/观测/checkpoint/HITL/Text2SQL/多Agent。**day30 补 v1 create_agent 入口注释；day37 清理陈旧合并备注** |
| 40 | MCP | ✅ 主题必需（JD 高频）。**修真 bug：代码连接不存在的 day31_mcp_server.py → day40_mcp_server.py，共 6 处** |
| 41-48 | 工程化：FastAPI/可靠性/成本/SQLite/Docker/Ollama/安全/pytest | ✅ 合理=LLMOps 需求。**day41/44/45/46/47 修引用漂移 9 处** |
| 49 | LoRA 一次性动手 | ✅ 保留。微调经验加薪 10-15%，"跑通一次+能讲清"的定位是对的 |
| 50 | RAG/Prompt/微调选型 | ✅ 合理，面试判断力题 |
| 51-61 | capstone 驱动文件（代码在 capstone/） | ✅ 合理，薄驱动是设计而非缺注释 |
| 62-66 | 上线补全：监控/pgvector/内容安全/供应商抽象/压测 | ✅ 合理。**day62 修引用漂移 1 处** |
| 67-71 | 智能客服 Agent（customer_service/，本次新增） | ✅ 补齐第二大企业场景 |
| 72-78 | 补充包：长期记忆/落盘/加固/子图/面试/提示/上下文 | ✅ 合理，day76 速查表对冲刺期高效 |

## 本次修改清单

1. **真 bug**（运行必挂）：day40_mcp_agent 连接不存在的 `day31_mcp_server.py`，含代码行 `"args"` 共 6 处 → day40。
2. **引用漂移 40 处**：day18/19/20/21/22（评测集编号整体 -1）、day37、day41（实际包的是 day12 不是 day10）、day44（checkpoint 在 35 不在 28）、day45（FastAPI 在 41）、day46/62（LangSmith 在 22 不在 21）、day47（/chat 在 41 不在 17）。
3. **BM25 中文分词失效**：默认按空格分词、中文整句=1 token，BM25 一路完全失效，因有向量兜底一直没暴露 → day14 与 capstone/knowledge_base.py 均加 bigram `preprocess_func` 修复并注明原理。
4. **技术时效补注**：langchain-community 2026-06 归档（day08/day14）；LangChain v1 推荐 `langchain.agents.create_agent`（day30）。

全部改动经 py_compile 验证，无语法错误；引用漂移复查为零残留。

## 遗留建议（不紧急）

- day24（742 行）/day25（519 行）偏长，冲刺期二刷时可只看头注释+小结。
- BM25 分词生产建议换 jieba（bigram 是零依赖的够用解）。
- 关注 FAISS/BM25Retriever 官方迁移公告（community 归档后暂无独立包）。

Sources: [AI Developer Hiring 2026](https://www.digitalapplied.com/blog/ai-developer-hiring-skills-that-matter-2026) · [KDnuggets LLM Engineer Roadmap](https://www.kdnuggets.com/the-roadmap-to-becoming-an-llm-engineer-in-2026) · [Sunsetting langchain-community #674](https://github.com/langchain-ai/langchain-community/issues/674) · [What's new in LangChain v1](https://docs.langchain.com/oss/python/releases/langchain-v1) · [LangChain/LangGraph 1.0](https://blog.langchain.com/langchain-langgraph-1dot0/)
