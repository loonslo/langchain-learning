# 3.6 LangSmith 追踪：让一次调用可以回放

[全书目录](../../README.md) · [上一章 3.5](../3.5-eval-dataset-ragas/README.md) · [下一章 3.7](../3.7-eval-regression-curve/README.md)

- **目标**：用 LangSmith 把一次 RAG 调用的每一步记成 trace，并把评测集传成 dataset 做在线评估。
- **前置**：2.6；3.4、3.5（在线评估需要 `eval_set_full.json`）；`DEEPSEEK_API_KEY`；本地 embedding 模型。
- **环境**：调用真实模型；`LANGSMITH_API_KEY` 可选，没配则跳过 LangSmith 部分。
- **命令**：`python tools/run_chapter.py 3.6`

## 问题

RAG 答错时，你想知道错在检索的哪一步、召回了什么、prompt 收到的上下文长什么样。本地算指标只告诉你“错了”，看不到过程。可观测性就是把每次调用的过程留成可以回放的证据。

## 概念

- **trace**：一次调用的完整记录：检索 → 拼上下文 → 生成，每一步的输入输出。设几个环境变量后，所有 LangChain / LangGraph 调用自动上报，不需要改业务代码。
- **dataset 与 experiment**：dataset 是评测集，experiment 是在它上面跑一遍被测系统并打分；同一 dataset 的多次 experiment 可以在网页里对比。
- **和本地评测的关系**：本地指标轻量、随手运行；LangSmith 适合团队协作、留存历史、看趋势。

## 流程

1. 配置了 `LANGSMITH_API_KEY` 时，设置 `LANGSMITH_TRACING` 等环境变量。
2. `trace_demo`：正常运行一次 RAG，这次调用的每一步会出现在 LangSmith 的 `rag-evaluation` 项目里。
3. `langsmith_eval`：读 `eval_set_full.json`（非拒答题），创建 dataset，用 `evaluate` 批量运行并用简化的关键词命中函数打分。
4. 没配 key 或没有评测集时，对应部分给出提示并跳过。

## 代码导读

[langsmith_eval.py](langsmith_eval.py)：先看开 trace 的几行环境变量，再看 `trace_demo`，最后看 `langsmith_eval` 里的 `target` 与评分函数。

## 练习

1. 配置密钥后运行，打开 LangSmith 找到这次的 trace，看 retriever 召回了哪些块、prompt 实际收到什么上下文。
2. 用 trace 区分一次失败是检索问题（召回里没有相关块）还是生成问题（召回对了但答偏）。
3. 把评分函数换成更严格的规则，比较两次 experiment。

## 运行与边界

- 上传到 LangSmith 会把问题、上下文和回答发到第三方服务，使用真实或私有数据前先确认范围。
- 在线评估的简化评分函数只是示例，不能代替校准过的评测。
