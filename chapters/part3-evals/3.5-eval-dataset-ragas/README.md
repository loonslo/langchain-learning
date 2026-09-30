# 3.5 Ragas 评测：理解指标实际需要的证据

[全书目录](../../README.md) · [上一章 3.4](../3.4-eval-dataset-build/README.md) · [下一章 3.6](../3.6-langsmith-eval/README.md)

- **目标**：补齐评测集（拒答题、引用题），合并成 25 条，并第一次用 RAGAS 评估。
- **前置**：3.4（先运行它生成 `eval_set.json`）。
- **环境**：合并部分离线；RAGAS 部分另需 `pip install ragas datasets`、`DEEPSEEK_API_KEY` 和本地 embedding 模型。
- **命令**：`python tools/run_chapter.py 3.5`

## 问题

只有事实题的评测集测不出“系统会不会乱答”。文档里没有的问题，正确行为是拒答；引用题则要求答对之外还要标对来源。同时，手写指标之外，也该认识业界通用的评测库。

## 概念

- **拒答题**：文档里完全没有答案的问题（8 条）。硬答就是幻觉，这类题直接量化“防幻觉防得住吗”，用 3.2 的拒答正确率计算，不进 RAGAS。
- **引用题**：答对还不够，得标对来源。
- **单一数据源**：合并产物 `eval_set_full.json` 是整条评测线的数据源，3.2、3.3、3.6、3.7 都读它。
- **RAGAS**：库函数自动计算 faithfulness（忠实度）、answer_relevancy（答案相关性）、context_precision（上下文精度）。它评的是有答案时的质量。默认使用 OpenAI，本章用 `LangchainLLMWrapper` 与 `LangchainEmbeddingsWrapper` 换成 DeepSeek + 本地 embedding。

## 流程

1. `load_or_build_full_set` 读取 3.4 的 `eval_set.json`，加上 `EXTRA`（8 条拒答 + 2 条引用），写出 `eval_set_full.json`，共 25 条。
2. 打印各题型数量。
3. `run_ragas` 对非拒答题：先跑一遍 RAG 收集 question、answer、contexts、ground_truth，再交给 RAGAS 评估。未安装 ragas 时给出安装提示，不报错。

## 代码导读

[dataset_ragas.py](dataset_ragas.py)：先看 `EXTRA` 里拒答题和引用题怎么写，再看合并函数，最后看 `run_ragas` 怎样准备 RAGAS 需要的数据。

## 练习

1. 运行合并，打开 `eval_set_full.json` 核对各题型数量。
2. 安装 RAGAS 后运行评估，记录三个指标。
3. 把 `chunk_size` 设得很大再评估，看 `context_precision` 是否下降（噪声多则精度降），用数字验证 2.7 的结论。

## 运行与边界

- RAGAS 评估会大量调用模型，费用较高。它也是 LLM 打分，有自己的偏差。
- 评测集 25 条只够演示，不足以下统计结论。
