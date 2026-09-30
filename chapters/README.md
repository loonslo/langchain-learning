# 章节总地图

从一次模型调用开始，逐步走到可评测的 RAG、可控的 Agent，再到一个企业客服应用。
第 0–6 篇是必修主线，第 7 篇是综合项目，第 8–10 篇按岗位选学。

每章的 README 依次回答：要解决什么问题、涉及哪些概念、代码怎么运转、从哪里读代码、怎么练习、边界在哪里。
建议先读 README，再运行和阅读代码；目录存在、离线测试通过和真实环境验收是三件事，要分别记录。

## 怎样运行

从仓库根目录运行。第 0–6 篇的独立脚本统一用：

```bash
python tools/run_chapter.py 1.1                    # 章节里只有一个脚本时，只写章节号
python tools/run_chapter.py 2.1 load_split.py      # 有多个脚本时，指定文件名
python tools/run_chapter.py 3.7 --no-upload        # 章节号（和脚本名）之后的参数原样传给脚本
```

- 入口会设置共享的导入路径，并把工作目录切到本章目录：脚本生成的文件（数据库、向量库、日志）都留在本章目录。
- 多章共用的资料放在 [shared-data](shared-data/README.md)（示例文档、评测集），路径由根目录的 `common.py` 提供，与工作目录无关。
- 第 7 篇和第 8–10 篇是累积项目，用 `tools/materialize.py` 还原成完整快照再运行，见各篇 README。
- 依赖：`python -m pip install -r requirements-course.txt`；先运行 `python tools/run_chapter.py 0.1` 自检，缺哪一篇的依赖会直接列出。

“运行环境”一列说明该章需要什么：**离线**不需要密钥或模型；**真实模型**需要 `DEEPSEEK_API_KEY` 并会产生少量费用；**本地 embedding** 需要下载 BGE 模型（见根目录 README“准备本地 embedding 模型”）。

## 怎样记录

每章有一份 `workbook.md`（学习记录）：先写预测，再运行，最后填实际结果、失败情形和未验证的部分。真实模型、离线替身、远端服务和部署结果要分别记录。方法见 [0.2](part0-setup/0.2-learning-workflow/README.md)。


## 第 0 篇：启程准备

先确认环境，再建立记录问题、过程和证据的方法。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 0.1 | [环境与离线自检](part0-setup/0.1-environment/README.md) | 离线 |
| 0.2 | [学习方法与验收记录](part0-setup/0.2-learning-workflow/README.md) | 无代码 |

## 第 1 篇：模型调用与上下文基础

从一次请求往返出发，依次理解输出、结构、历史与工具，最后组合成对话练习。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 1.1 | [首次模型调用：让一条请求往返](part1-foundations/1.1-first-call/README.md) | 真实模型 |
| 1.2 | [控制输出：要求、随机性与流式回复](part1-foundations/1.2-control-output/README.md) | 真实模型 |
| 1.3 | [结构化输出：让程序读懂模型的回答](part1-foundations/1.3-structured-output/README.md) | 真实模型 |
| 1.4 | [多轮上下文：记住谁说过什么](part1-foundations/1.4-context-memory/README.md) | 真实模型 |
| 1.5 | [工具调用：由程序完成事实查询和计算](part1-foundations/1.5-tool-calling/README.md) | 真实模型 |
| 1.6 | [MCP 入门：先连通一项工具](part1-foundations/1.6-mcp-intro/README.md) | 离线，最小示例 |
| 1.7 | [LLM 原理认知：理解能力来源和边界](part1-foundations/1.7-llm-internals/README.md) | 本地 embedding |
| 1.8 | [综合练习：会话与工具如何协作](part1-foundations/1.8-cli-chatbot/README.md) | 真实模型，交互式 |

## 第 2 篇：检索增强生成 RAG

先把资料读对并找到证据，再组织回答。每次增加切分、融合、改写或重排，都保留固定问题作比较。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 2.1 | [文档加载与切分：资料如何进入系统](part2-rag/2.1-load-split/README.md) | 离线 |
| 2.2 | [向量化与召回：先找到可能相关的片段](part2-rag/2.2-embed-retrieve/README.md) | 本地 embedding |
| 2.3 | [最小 RAG：让回答依据检索资料](part2-rag/2.3-minimal-rag/README.md) | 真实模型 + 本地 embedding |
| 2.4 | [RAG 评测种子：从五个问题开始](part2-rag/2.4-eval-seed/README.md) | 离线 |
| 2.5 | [裸 SDK 与循环：看清框架封装了什么](part2-rag/2.5-raw-sdk-rag-agent-loop/README.md) | 离线可读，有密钥时调用模型 |
| 2.6 | [PDF 与来源溯源：答案要能回到原文](part2-rag/2.6-pdf-sources/README.md) | 真实模型 + 本地 embedding |
| 2.7 | [切分策略：让完整事实留在片段里](part2-rag/2.7-chunk-strategy/README.md) | 本地 embedding |
| 2.8 | [混合检索：同时照顾语义和精确词](part2-rag/2.8-hybrid-search/README.md) | 本地 embedding |
| 2.9 | [查询改写：把用户的话转成更好检索的问题](part2-rag/2.9-query-rewrite/README.md) | 真实模型 + 本地 embedding |
| 2.10 | [向量库持久化：下次启动不再从头建立](part2-rag/2.10-chroma-persist/README.md) | 本地 embedding |
| 2.11 | [重排与多模态：增加能力后仍要保留证据](part2-rag/2.11-multimodal-rerank/README.md) | 本地 reranker，多模态部分选做 |

## 第 3 篇：评测方法论

从失败过程与小题集出发，理解规则、模型评委、数据工程和回归对比，把分数转成有证据的改动。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 3.1 | [失败分析：先找到最早出错的环节](part3-evals/3.1-error-analysis/README.md) | 离线 |
| 3.2 | [基础评测：把预期拆成可以判断的项](part3-evals/3.2-eval-basics/README.md) | 真实模型 |
| 3.3 | [LLM 评委：让语义判断也能被复查](part3-evals/3.3-llm-judge/README.md) | 真实模型 |
| 3.4 | [评测数据建设：把业务覆盖写成样本](part3-evals/3.4-eval-dataset-build/README.md) | 离线 |
| 3.5 | [Ragas 评测：理解指标实际需要的证据](part3-evals/3.5-eval-dataset-ragas/README.md) | 合并离线，RAGAS 需真实模型 |
| 3.6 | [LangSmith 追踪：让一次调用可以回放](part3-evals/3.6-langsmith-eval/README.md) | 真实模型，LangSmith 可选 |
| 3.7 | [回归曲线：看见改动带来的收益与退化](part3-evals/3.7-eval-regression-curve/README.md) | 真实模型 |
| 3.8 | [提示词 A/B 对比：用固定问题检验修改](part3-evals/3.8-prompt-ab-judge/README.md) | 真实模型 + LangSmith |
| 3.9 | [Agent 轨迹评测：结果正确还不够](part3-evals/3.9-agent-trajectory-eval/README.md) | 离线 |
| 3.10 | [失败诊断：把结果转成下一次改动](part3-evals/3.10-eval-report-failures/README.md) | 离线，live 模式需真实模型 |

## 第 4 篇：Agent 与 LangGraph

先判断是否需要模型决策，再学习状态、节点、分支、合并、恢复与协作。每个循环都要说明失败和终止。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 4.1 | [Agent 模式：先决定控制权放在哪里](part4-agents-langgraph/4.1-agent-patterns/README.md) | 离线 |
| 4.2 | [LangGraph 基础：一份状态经过两个节点](part4-agents-langgraph/4.2-langgraph-basics/README.md) | 离线 |
| 4.3 | [分支与循环：每条路线都要有出口](part4-agents-langgraph/4.3-branch-loop/README.md) | 离线 + 真实模型 |
| 4.4 | [状态合并与 Reducer：并行结果如何留下来](part4-agents-langgraph/4.4-state-reducer/README.md) | 离线 |
| 4.5 | [ReAct 工具循环：观察结果后再决定下一步](part4-agents-langgraph/4.5-react-agent/README.md) | 离线 + 真实模型 |
| 4.6 | [节点可靠性：失败之后如何继续](part4-agents-langgraph/4.6-node-reliability/README.md) | 离线，一处需真实模型 |
| 4.7 | [结构化路由：把模型选择限制在可验证集合](part4-agents-langgraph/4.7-structured-routing/README.md) | 真实模型 |
| 4.8 | [规划与执行：让计划进度成为显式状态](part4-agents-langgraph/4.8-plan-and-execute/README.md) | 离线 + 真实模型 |
| 4.9 | [可观测性：把运行过程留成证据](part4-agents-langgraph/4.9-observability/README.md) | 离线 |
| 4.10 | [检查点与上下文：恢复流程和管理对话](part4-agents-langgraph/4.10-checkpoint-context/README.md) | 真实模型 |
| 4.11 | [流式与人工介入：暂停在需要决定的位置](part4-agents-langgraph/4.11-streaming-hitl/README.md) | 离线，需终端输入 |
| 4.12 | [搜索工具与信任边界：资料不能替你发号施令](part4-agents-langgraph/4.12-tool-safety-search/README.md) | 真实模型 |
| 4.13 | [Text2SQL：先验证查询，再访问结构化数据](part4-agents-langgraph/4.13-text2sql-agent/README.md) | 离线 |
| 4.14 | [Supervisor 与并行：多角色协作需要明确交接](part4-agents-langgraph/4.14-supervisor-fanout/README.md) | 真实模型 |
| 4.15 | [框架取舍：先写需求，再选择工具](part4-agents-langgraph/4.15-framework-landscape/README.md) | 无代码 |

## 第 5 篇：服务化与工程可靠性

把脚本推进到接口、持久化、可观测与回归，逐项理解真实服务需要的边界。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 5.1 | [FastAPI 服务：让模型能力成为接口](part5-production/5.1-serve-fastapi/README.md) | 真实模型 + 本地 embedding |
| 5.2 | [超时、重试与成本统计：可靠也要有预算](part5-production/5.2-reliability-retry/README.md) | 真实模型 |
| 5.3 | [成本、缓存与路由：收益需要实际测量](part5-production/5.3-cost-cache-routing/README.md) | 真实模型 |
| 5.4 | [SQLite 持久化：把问答变成可查询记录](part5-production/5.4-sqlite-persistence/README.md) | 离线 |
| 5.5 | [容器与运行配置：交付的不只是代码](part5-production/5.5-docker-packaging/README.md) | 离线，构建镜像需 Docker |
| 5.6 | [调用日志与 Ollama 本地推理：先记录，再换到本机](part5-production/5.6-ollama-inference/README.md) | 真实模型 |
| 5.7 | [安全护栏：把信任边界写进程序](part5-production/5.7-security-guardrails/README.md) | 离线 |
| 5.8 | [pytest 回归：让已知质量问题自动报警](part5-production/5.8-pytest-regression/README.md) | 真实模型 |

## 第 6 篇：模型方案取舍

从问题原因选择 Prompt、RAG 或微调；LoRA 实操按硬件和数据条件选做。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 6.1 | [Prompt、RAG 与微调：问题不同，方案也不同](part6-model-tradeoffs/6.1-choose-prompt-rag-finetune/README.md) | 离线 |
| 6.2 | [LoRA 微调选修：训练、验证与重新加载](part6-model-tradeoffs/6.2-lora-finetune-optional/README.md) | 选做，依赖较重 |

## 第 7 篇：企业客服 Copilot

[进入 8 个里程碑的项目教程](../flagship-project/README.md)。29 个步骤连续完善同一个业务：先还原完整快照，再核对累计测试。它对应的目录是仓库根目录下的 `flagship-project/`，不在 `chapters/` 里。[capstone](../capstone/README.md) 是另一个能力整合实现，两者分别验收。

## 第 8 篇：AI 质量工程专项（选修）

将测试背景转化为风险、数据、契约、检索、轨迹和发布门禁能力。这是一条独立累积的测试工具项目线。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 8.1 | [AI 测试策略：先找业务风险](part8-ai-quality-optional/8.1-risk-modeling/README.md) | 离线测试 |
| 8.2 | [评测数据工程：数据也要有契约](part8-ai-quality-optional/8.2-eval-data-engineering/README.md) | 离线测试 |
| 8.3 | [Mock、契约与不变量：不同测试保护不同边界](part8-ai-quality-optional/8.3-mock-contract-invariant/README.md) | 离线测试 |
| 8.4 | [RAG 分层测试：召回、排名和引用分别检查](part8-ai-quality-optional/8.4-rag-layered-testing/README.md) | 离线测试 |
| 8.5 | [Judge 校准：先证明测量工具可信](part8-ai-quality-optional/8.5-judge-calibration/README.md) | 离线测试 |
| 8.6 | [Agent 自动化测试：约束动作而不只看答案](part8-ai-quality-optional/8.6-agent-trajectory-testing/README.md) | 离线测试 |
| 8.7 | [API、SSE 与端到端：用户到底收到了什么](part8-ai-quality-optional/8.7-api-sse-e2e/README.md) | 离线测试 |
| 8.8 | [安全、韧性与性能：一起验证服务预算](part8-ai-quality-optional/8.8-security-resilience-perf/README.md) | 离线测试 |
| 8.9 | [CI 分层门禁：结果缺失也不能默认为通过](part8-ai-quality-optional/8.9-ci-layered-gate/README.md) | 离线测试 |
| 8.10 | [线上反馈闭环：审查后再加入回归](part8-ai-quality-optional/8.10-production-feedback-loop/README.md) | 离线测试 |

## 第 9 篇：企业数据与推理设施专项（选修）

建立意图与会话契约，再理解数据库隔离、缓存、检索后端和推理服务。外部依赖的真实验证另记。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 9.1 | [Few-shot 意图识别：先统一业务类别](part9-enterprise-infra-optional/9.1-intent-fewshot/README.md) | 离线测试，真实服务另验 |
| 9.2 | [槽位与追问：只补真正缺少的信息](part9-enterprise-infra-optional/9.2-slot-filling/README.md) | 离线测试，真实服务另验 |
| 9.3 | [稳定 JSON 边界：解析失败也有明确出口](part9-enterprise-infra-optional/9.3-stable-json-output/README.md) | 离线测试，真实服务另验 |
| 9.4 | [意图工作流：把理解结果接到业务](part9-enterprise-infra-optional/9.4-intent-workflow/README.md) | 离线测试，真实服务另验 |
| 9.5 | [PostgreSQL 与 RLS：数据库也要知道租户](part9-enterprise-infra-optional/9.5-postgres-rls/README.md) | 离线测试，真实服务另验 |
| 9.6 | [只读查询目录与执行计划：安全也包括成本](part9-enterprise-infra-optional/9.6-readonly-sql-explain/README.md) | 离线测试，真实服务另验 |
| 9.7 | [Redis 缓存与限流：先定义失效条件](part9-enterprise-infra-optional/9.7-redis-cache-ratelimit/README.md) | 离线测试，真实服务另验 |
| 9.8 | [向量存储选型：把需求写成判断依据](part9-enterprise-infra-optional/9.8-vectorstore-selection/README.md) | 离线测试，真实服务另验 |
| 9.9 | [Compose 与运维：依赖也进入交付清单](part9-enterprise-infra-optional/9.9-compose-linux-ops/README.md) | 离线测试，真实服务另验 |
| 9.10 | [兼容模型接口：配置相同也要核对能力](part9-enterprise-infra-optional/9.10-openai-compatible-provider/README.md) | 离线测试，真实服务另验 |
| 9.11 | [vLLM 选修：服务配置先于 GPU 实验](part9-enterprise-infra-optional/9.11-vllm-gpu/README.md) | 离线测试，真实服务另验 |
| 9.12 | [推理基准：先过质量，再比较容量](part9-enterprise-infra-optional/9.12-inference-benchmark/README.md) | 离线测试，真实服务另验 |

## 第 10 篇：MCP 鉴权与 A2A（选修）

从可信工具授权走向独立 Agent 的任务协作，区分协议模型、离线测试与真实远端互操作。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 10.1 | [MCP 授权与审批：工具连接后还要检查身份](part10-mcp-a2a-optional/10.1-mcp-auth-approval/README.md) | 离线测试 |
| 10.2 | [A2A 任务生命周期：远端协作需要可追踪状态](part10-mcp-a2a-optional/10.2-a2a-agent-card-task/README.md) | 离线测试 |
| 10.3 | [A2A HTTP 边界：协议形状和任务语义一起校验](part10-mcp-a2a-optional/10.3-a2a-protocol-bindings/README.md) | 离线测试 |
| 10.4 | [跨 Agent 集成：把委托落到受控订单读取](part10-mcp-a2a-optional/10.4-cross-agent-delegation/README.md) | 离线测试 |

## 第 7 篇之后怎么选

- 想把测试经验转成 AI 质量工程能力：第 8 篇。
- 想补企业级数据、缓存、检索后端和推理服务：第 9 篇。
- 想了解 MCP 鉴权和 Agent 之间的协作：第 10 篇。
