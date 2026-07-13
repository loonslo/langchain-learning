# LangChain 学习项目（主项目）

**目标**：测试工程师 → AI Agent 应用开发，2~3 个月内完成并跳槽。

**结构**：Day1-71 每日一个自包含 Python 文件 + capstone 毕业项目。
- Day1-6 基础（chat/结构化输出/memory/tool calling）
- Day7-17 RAG（加载切分、混合检索、rerank、Chroma 持久化）
- Day18-26 评估（LLM judge、ragas、回归曲线、A/B、失败分析）← 护城河
- Day28-40 LangGraph / Agent（ReAct、plan-execute、HITL、text2SQL、MCP）
- Day41+ 工程化（FastAPI、可靠性、Docker、CI）
- capstone：企业知识库 Agent + 评估平台（认证、多租户、监控、增量同步）

**判断标准**（来自项目指令）：只保留高效、以转行为第一性目标的代码和任务；去掉无关低效的部分。

**关键命令**：见 CLAUDE.md。测试用 pytest，评估平台默认离线可跑。
