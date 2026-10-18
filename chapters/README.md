# 章节总地图

从一次模型调用开始，逐步走到可评测的 RAG、可控的 Agent，再到一个企业客服应用。
第 0–6 篇是必修主线，第 7 篇是综合项目，第 8–10 篇按岗位选学。

每章的 README 依次回答：要解决什么问题、涉及哪些概念、代码怎么运转、从哪里读代码、怎么练习、边界在哪里。
建议先读 README，再运行和阅读代码；目录存在、离线测试通过和真实环境验收是三件事，要分别记录。

> 岗位对标与 12 周核心路径提案见 [docs/curriculum-v2.md](../docs/curriculum-v2.md)（提案，未替代下列顺序）。
>
> 82 章全部有验收方式：75 章用 `gate/gate_check.py` 闭卷 gate，7 章（0.1、0.2、1.6、1.7、3.6、4.15、5.6）用 `gate/CHECKLIST.md` 清单验收。先读各章 README 的任务书；gate 全部 PASS 后再打开参考实现。项目 29 步用 [flagship-project/ACCEPTANCE.md](../flagship-project/ACCEPTANCE.md) 总清单验收。
>
> 标题里的 `Lx` 是 v2 路径编号；章节号（如 2.5）仍是现有目录号，旧链接继续有效。

## v2 路径速查

每章标题下都有一行 `v2 路径`，写明阶段、必做/选做和跨篇顺序。速查：

| v2 阶段 | 对应章节 | 定位 |
|---|---|---|
| L0 定位与基线 | 0.1–0.2 | 核心 |
| L1 模型调用与 Harness | 1.1–1.8、2.5 | 核心；1.1–1.5、1.8、2.5 是 Gate |
| L2 RAG 与上下文 | 2.1–2.11（全部 Gate；2.5 归 L1） | 核心；2.11 多模态部分选做 |
| L3 评测与质量 | 3.1–3.10 | 核心；3.1–3.5、3.7、3.10 已 Gate，3.6 清单，3.9 建议放到 4.10 后学 |
| L4 Agent 与工作流 | 4.1–4.15、3.9 | 核心；4.1–4.12、4.14、3.9 已 Gate，4.13 选做 |
| L5 服务化与生产 | 5.1–5.8、6.1 | 核心；5.1–5.5、5.7、5.8 已 Gate，5.6 选做 |
| L6 项目与求职 | 7.8、capstone | 项目与求职 |
| 选修专项 | 6.2、8.x、9.x、10.x | 选做；8.5/8.6/8.9/9.5 可作核心阅读 |

跨篇顺序以 `v2 路径` 为准，不要只看目录号：

- **2.4 / 2.5**：先学 2.5（L1.6 手写 Harness），再做 2.4（L2.9 评测 Gate）；两者都不依赖对方。
- **3.9**：合成轨迹可先当预习，真正做轨迹评测放在 4.10/4.11 之后。
- **5.2**：先通过 5.1 的 Gate，再读 5.2 的 jitter、主备切换和真实成本。
- **9.1 / 10.1**：`前置` 里的 8.10 / 9.12 是**运行累积代码**的还原顺序，不是学习前置；不想跑整条线时，可直接读概念，不必先做完整条选修线。

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
| 0.1 | [环境与离线自检（清单）](part0-setup/0.1-environment/README.md) | 清单验收 |
| 0.2 | [学习方法与验收记录（清单）](part0-setup/0.2-learning-workflow/README.md) | 清单验收 |

## 第 1 篇：模型调用与上下文基础

从一次请求往返出发，依次理解输出、结构、历史与工具，最后组合成对话练习。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 1.1 | [L1.1 一次调用（Gate）](part1-foundations/1.1-first-call/README.md) | 离线 gate；参考实现需真实模型 |
| 1.2 | [L1.2 输出控制（Gate）](part1-foundations/1.2-control-output/README.md) | 离线 gate；参考实现需真实模型 |
| 1.3 | [L1.3 结构化输出（Gate）](part1-foundations/1.3-structured-output/README.md) | 离线 gate；参考实现需真实模型 |
| 1.4 | [L1.4 上下文与记忆（Gate）](part1-foundations/1.4-context-memory/README.md) | 离线 gate；参考实现需真实模型 |
| 1.5 | [L1.5 工具调用（Gate）](part1-foundations/1.5-tool-calling/README.md) | 离线 gate；参考实现需真实模型 |
| 1.6 | [MCP 入门（清单）](part1-foundations/1.6-mcp-intro/README.md) | 清单验收 |
| 1.7 | [LLM 原理认知（清单）](part1-foundations/1.7-llm-internals/README.md) | 清单验收 |
| 1.8 | [L1.7 CLI 助手（Gate）](part1-foundations/1.8-cli-chatbot/README.md) | 离线 gate；参考实现需真实模型 |

## 第 2 篇：检索增强生成 RAG

先把资料读对并找到证据，再组织回答。每次增加切分、融合、改写或重排，都保留固定问题作比较。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 2.1 | [L2.1 加载与切分（Gate）](part2-rag/2.1-load-split/README.md) | 离线 gate；参考实现离线 |
| 2.2 | [L2.2 向量化与召回（Gate）](part2-rag/2.2-embed-retrieve/README.md) | 离线 gate；参考实现需本地 embedding |
| 2.3 | [L2.3 最小 RAG（Gate）](part2-rag/2.3-minimal-rag/README.md) | 离线 gate；参考实现需真实模型 + embedding |
| 2.4 | [L2.9 RAG 评测基线（Gate）](part2-rag/2.4-eval-seed/README.md) | 离线 gate |
| 2.5 | [L1.6 手写 Harness（Gate）](part2-rag/2.5-raw-sdk-rag-agent-loop/README.md) | 离线 gate，参考实现可选真实模型 |
| 2.6 | [L2.3 扩展：PDF 与来源（Gate）](part2-rag/2.6-pdf-sources/README.md) | 离线 gate；参考实现需真实模型 + embedding |
| 2.7 | [L2.4 切分策略（Gate）](part2-rag/2.7-chunk-strategy/README.md) | 离线 gate；参考实现需本地 embedding |
| 2.8 | [L2.5 混合检索（Gate）](part2-rag/2.8-hybrid-search/README.md) | 离线 gate；参考实现需本地 embedding |
| 2.9 | [L2.6 查询改写（Gate）](part2-rag/2.9-query-rewrite/README.md) | 离线 gate；参考实现需真实模型 + embedding |
| 2.10 | [L2.7 向量库持久化（Gate）](part2-rag/2.10-chroma-persist/README.md) | 离线 gate；参考实现需本地 embedding |
| 2.11 | [L2.8 重排与多模态（Gate）](part2-rag/2.11-multimodal-rerank/README.md) | 离线 gate；参考实现需 reranker，多模态选做 |

## 第 3 篇：评测方法论

从失败过程与小题集出发，理解规则、模型评委、数据工程和回归对比，把分数转成有证据的改动。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 3.1 | [L3.1 失败分析（Gate）](part3-evals/3.1-error-analysis/README.md) | 离线 gate |
| 3.2 | [L3.3 基础评测（Gate）](part3-evals/3.2-eval-basics/README.md) | 离线 gate；参考实现需真实模型 |
| 3.3 | [L3.4 LLM Judge 与校准（Gate）](part3-evals/3.3-llm-judge/README.md) | 离线 gate，参考实现可选真实模型 |
| 3.4 | [L3.2 评测集建设（Gate）](part3-evals/3.4-eval-dataset-build/README.md) | 离线 gate |
| 3.5 | [L3.5 Ragas 与指标口径（Gate）](part3-evals/3.5-eval-dataset-ragas/README.md) | 离线 gate；参考实现 RAGAS 需真实模型 |
| 3.6 | [L3.6 LangSmith 可观测性（清单）](part3-evals/3.6-langsmith-eval/README.md) | 外部服务，清单验收 |
| 3.7 | [L3.6 回归对比（Gate）](part3-evals/3.7-eval-regression-curve/README.md) | 离线 gate；参考实现需真实模型 |
| 3.8 | [L3.6 扩展：Prompt A/B 指标（Gate）](part3-evals/3.8-prompt-ab-judge/README.md) | 离线 gate；真实 A/B 需模型 |
| 3.9 | [L4.11 Agent 轨迹评测（Gate）](part3-evals/3.9-agent-trajectory-eval/README.md) | 离线 gate |
| 3.10 | [L3.6 扩展：失败诊断（Gate）](part3-evals/3.10-eval-report-failures/README.md) | 离线 gate；live 模式需真实模型 |

## 第 4 篇：Agent 与 LangGraph

先判断是否需要模型决策，再学习状态、节点、分支、合并、恢复与协作。每个循环都要说明失败和终止。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 4.1 | [L4.1 Agent 模式（Gate）](part4-agents-langgraph/4.1-agent-patterns/README.md) | 离线 gate |
| 4.2 | [L4.2 LangGraph 基础（Gate）](part4-agents-langgraph/4.2-langgraph-basics/README.md) | 离线 gate |
| 4.3 | [L4.3 分支与循环（Gate）](part4-agents-langgraph/4.3-branch-loop/README.md) | 离线 gate；参考实现后半段需真实模型 |
| 4.4 | [L4.3 状态与 Reducer（Gate）](part4-agents-langgraph/4.4-state-reducer/README.md) | 离线 gate |
| 4.5 | [L4.4 ReAct 与工具设计（Gate）](part4-agents-langgraph/4.5-react-agent/README.md) | 离线 gate，参考实现可选真实模型 |
| 4.6 | [L4.3 扩展：节点可靠性（Gate）](part4-agents-langgraph/4.6-node-reliability/README.md) | 离线 gate；参考实现一处需真实模型 |
| 4.7 | [L4.5 结构化路由（Gate）](part4-agents-langgraph/4.7-structured-routing/README.md) | 离线 gate；参考实现需真实模型 |
| 4.8 | [L4.5 扩展：规划与执行（Gate）](part4-agents-langgraph/4.8-plan-and-execute/README.md) | 离线 gate；参考实现需真实模型 |
| 4.9 | [L5.6 可观测性（Gate）](part4-agents-langgraph/4.9-observability/README.md) | 离线 gate |
| 4.10 | [L4.6 检查点与上下文（Gate）](part4-agents-langgraph/4.10-checkpoint-context/README.md) | 离线 gate；参考实现需真实模型 |
| 4.11 | [L4.10 流式与人工介入（Gate）](part4-agents-langgraph/4.11-streaming-hitl/README.md) | 离线 gate |
| 4.12 | [L4.10 搜索信任边界（Gate）](part4-agents-langgraph/4.12-tool-safety-search/README.md) | 离线 gate；参考实现需真实模型 |
| 4.13 | [L4.12 Text2SQL 安全门（Gate）](part4-agents-langgraph/4.13-text2sql-agent/README.md) | 离线 gate |
| 4.14 | [L4.9 Supervisor 与并行（Gate）](part4-agents-langgraph/4.14-supervisor-fanout/README.md) | 离线 gate；参考实现需真实模型 |
| 4.15 | [框架取舍（清单）](part4-agents-langgraph/4.15-framework-landscape/README.md) | 清单验收 |

## 第 5 篇：服务化与工程可靠性

把脚本推进到接口、持久化、可观测与回归，逐项理解真实服务需要的边界。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 5.1 | [L5.1 FastAPI 服务与可靠性（Gate）](part5-production/5.1-serve-fastapi/README.md) | 离线 gate，参考实现需真实模型 |
| 5.2 | [L5.2 可靠性：退避/重试/成本（Gate）](part5-production/5.2-reliability-retry/README.md) | 离线 gate；参考实现需真实模型 |
| 5.3 | [L5.2 扩展：成本/缓存/路由（Gate）](part5-production/5.3-cost-cache-routing/README.md) | 离线 gate；参考实现需真实模型 |
| 5.4 | [L5.4 SQLite 持久化（Gate）](part5-production/5.4-sqlite-persistence/README.md) | 离线 gate |
| 5.5 | [L5.7 容器与配置（Gate）](part5-production/5.5-docker-packaging/README.md) | 离线 gate；真实构建需 Docker |
| 5.6 | [调用日志与 Ollama 本地推理（清单）](part5-production/5.6-ollama-inference/README.md) | 清单验收（外部服务） |
| 5.7 | [L5.4 安全护栏（Gate）](part5-production/5.7-security-guardrails/README.md) | 离线 gate |
| 5.8 | [L3.3 扩展：pytest 回归（Gate）](part5-production/5.8-pytest-regression/README.md) | 离线 gate；真实回归需模型 |

## 第 6 篇：模型方案取舍

从问题原因选择 Prompt、RAG 或微调；LoRA 实操按硬件和数据条件选做。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 6.1 | [L5.10 方案选型（Gate）](part6-model-tradeoffs/6.1-choose-prompt-rag-finetune/README.md) | 离线 gate |
| 6.2 | [L6 LoRA 质量门禁（Gate）](part6-model-tradeoffs/6.2-lora-finetune-optional/README.md) | 离线 gate；真实训练需重依赖 |

## 第 7 篇：企业客服 Copilot

[进入 8 个里程碑的项目教程](../flagship-project/README.md)。29 个步骤连续完善同一个业务：先还原完整快照，再核对累计测试。它对应的目录是仓库根目录下的 `flagship-project/`，不在 `chapters/` 里。[capstone](../capstone/README.md) 是另一个能力整合实现，两者分别验收。

## 第 8 篇：AI 质量工程专项（选修）

将测试背景转化为风险、数据、契约、检索、轨迹和发布门禁能力。这是一条独立累积的测试工具项目线。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 8.1 | [L8 风险建模（Gate）](part8-ai-quality-optional/8.1-risk-modeling/README.md) | 离线 gate |
| 8.2 | [L8 评测数据工程（Gate）](part8-ai-quality-optional/8.2-eval-data-engineering/README.md) | 离线 gate |
| 8.3 | [L8 契约与不变量（Gate）](part8-ai-quality-optional/8.3-mock-contract-invariant/README.md) | 离线 gate |
| 8.4 | [L8 RAG 分层检索评测（Gate）](part8-ai-quality-optional/8.4-rag-layered-testing/README.md) | 离线 gate |
| 8.5 | [L3.4 扩展：Judge 校准（Gate）](part8-ai-quality-optional/8.5-judge-calibration/README.md) | 离线 gate |
| 8.6 | [L4.11 扩展：Agent 轨迹测试（Gate）](part8-ai-quality-optional/8.6-agent-trajectory-testing/README.md) | 离线 gate |
| 8.7 | [L8 API/SSE E2E（Gate）](part8-ai-quality-optional/8.7-api-sse-e2e/README.md) | 离线 gate |
| 8.8 | [L8 安全/韧性/性能（Gate）](part8-ai-quality-optional/8.8-security-resilience-perf/README.md) | 离线 gate |
| 8.9 | [L5.7 扩展：CI 分层门禁（Gate）](part8-ai-quality-optional/8.9-ci-layered-gate/README.md) | 离线 gate |
| 8.10 | [L3.7 反馈闭环（Gate）](part8-ai-quality-optional/8.10-production-feedback-loop/README.md) | 离线 gate |

## 第 9 篇：企业数据与推理设施专项（选修）

建立意图与会话契约，再理解数据库隔离、缓存、检索后端和推理服务。外部依赖的真实验证另记。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 9.1 | [L9 Few-shot 意图识别（Gate）](part9-enterprise-infra-optional/9.1-intent-fewshot/README.md) | 离线 gate |
| 9.2 | [L9 槽位填充（Gate）](part9-enterprise-infra-optional/9.2-slot-filling/README.md) | 离线 gate |
| 9.3 | [L9 稳定 JSON 契约（Gate）](part9-enterprise-infra-optional/9.3-stable-json-output/README.md) | 离线 gate |
| 9.4 | [L9 意图工作流（Gate）](part9-enterprise-infra-optional/9.4-intent-workflow/README.md) | 离线 gate |
| 9.5 | [L5.4 扩展：Postgres 与 RLS（Gate）](part9-enterprise-infra-optional/9.5-postgres-rls/README.md) | 离线 gate |
| 9.6 | [L9 只读 SQL 护栏（Gate）](part9-enterprise-infra-optional/9.6-readonly-sql-explain/README.md) | 离线 gate |
| 9.7 | [L5.2 扩展：Redis 缓存/限流（Gate）](part9-enterprise-infra-optional/9.7-redis-cache-ratelimit/README.md) | 离线 gate |
| 9.8 | [L9 向量存储选型（Gate）](part9-enterprise-infra-optional/9.8-vectorstore-selection/README.md) | 离线 gate |
| 9.9 | [L9 Compose 与运维（Gate）](part9-enterprise-infra-optional/9.9-compose-linux-ops/README.md) | 离线 gate |
| 9.10 | [L5.10 兼容模型配置（Gate）](part9-enterprise-infra-optional/9.10-openai-compatible-provider/README.md) | 离线 gate |
| 9.11 | [L9 vLLM 启动配置（Gate）](part9-enterprise-infra-optional/9.11-vllm-gpu/README.md) | 离线 gate |
| 9.12 | [L5.8 扩展：推理基准（Gate）](part9-enterprise-infra-optional/9.12-inference-benchmark/README.md) | 离线 gate |

## 第 10 篇：MCP 鉴权与 A2A（选修）

从可信工具授权走向独立 Agent 的任务协作，区分协议模型、离线测试与真实远端互操作。

| 章节 | 文字教程 | 运行环境 |
|---|---|---|
| 10.1 | [L4.9 MCP 授权与审批（Gate）](part10-mcp-a2a-optional/10.1-mcp-auth-approval/README.md) | 离线 gate |
| 10.2 | [L10 A2A 任务生命周期（Gate）](part10-mcp-a2a-optional/10.2-a2a-agent-card-task/README.md) | 离线 gate |
| 10.3 | [L10 A2A JSON-RPC 绑定（Gate）](part10-mcp-a2a-optional/10.3-a2a-protocol-bindings/README.md) | 离线 gate |
| 10.4 | [L10 跨 Agent 委派（Gate）](part10-mcp-a2a-optional/10.4-cross-agent-delegation/README.md) | 离线 gate |

## 第 7 篇之后怎么选

- 想把测试经验转成 AI 质量工程能力：第 8 篇。
- 想补企业级数据、缓存、检索后端和推理服务：第 9 篇。
- 想了解 MCP 鉴权和 Agent 之间的协作：第 10 篇。
