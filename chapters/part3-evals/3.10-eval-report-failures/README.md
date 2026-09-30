# 3.10 失败诊断：把结果转成下一次改动

[全书目录](../../README.md) · [上一章 3.9](../3.9-agent-trajectory-eval/README.md) · [下一章 4.1](../../part4-agents-langgraph/4.1-agent-patterns/README.md)

- **目标**：把失败样本按环节分组，得到“这条失败坏在哪一层”的证据，而不是只看总分。
- **前置**：3.7（可选，用来生成真实失败库）。
- **环境**：默认离线，使用本章自带的合成样本；二级复核（live 模式）另需 `pip install deepeval` 和 `DEEPSEEK_API_KEY`。
- **命令**：`python tools/run_chapter.py 3.10`

## 问题

评测分数告诉你“错了多少”，不告诉你“错在哪”。把结果转成下一次改动，要先分清失败属于拒答逻辑、检索、引用，还是生成。

## 概念

- **只诊断，不判决**：本章只回答“坏在哪一层”。发布门禁由 `capstone/ci_gate.py` 和 CI 工作流负责（7.6 / step1），两套判决会分叉。
- **一级分流**：用已算好的硬指标（`refusal_ok`、`keyword_score`、`citation_score`）给失败分组，标注“疑似层”。硬指标比对的是字符串，测不准语义，所以只分组、不下结论。便宜，不需要密钥。
- **二级复核（live）**：用 DeepEval 的三个维度分（Faithfulness、AnswerRelevancy、ContextualPrecision）复核，需要真实的 `retrieval_context`。缺参考答案时跳过 ContextualPrecision 并标注，不拿空字符串算分。DeepEval 也是 LLM 打分，结论只作证据和建议。
- **失败库的来源**：`--input` 指定的文件 → `chapters/shared-data/failures.json`（3.7 加 `--write-failures` 生成）→ 本章自带的 `failures_sample.json`（合成，无召回上下文，只能做一级分流）。

## 流程

1. 选定失败库，筛出 `passed` 为假的记录，并按是否携带 `retrieval_context` 推断模式（live 或 offline）。
2. `classify_by_hard_metrics` 依次判断：拒答逻辑 → 检索/引用 → 生成 → 其他。
3. live 模式下，对有上下文的失败样本调用 DeepEval，`dims_to_evidence` 把低分翻译成证据；`--limit` 控制复核条数。
4. 打印每条失败的问题、回答、参考答案和证据，汇总根因分布，写入本章 `reports/failure_diagnosis.json`。

## 代码导读

[failure_diagnosis.py](failure_diagnosis.py)：先读 `load_failures` 与 `classify_by_hard_metrics`（一级分流），再读 `measure_with_deepeval`（二级复核），最后读 `run_diagnosis` 的输出与汇总。[failures_sample.json](failures_sample.json) 是 7 条合成记录，其中 1 条已通过，用于展示筛选。

## 练习

1. 运行默认样本，查看每类“疑似层”的建议，解释为什么硬指标只能分组不能定案。
2. 运行 3.7（加 `--write-failures`）生成真实失败库，再运行本章，比较与合成样本的差别。
3. 安装 DeepEval 后用 `--mode live --limit 3` 复核，比较一级分流与维度分是否一致。

## 运行与边界

- 合成样本只用于理解规则，其中的回答是虚构的，不代表真实系统。
- live 模式会调用模型并产生费用，先用 `--limit` 控制条数。
- 失败样本可能含私有问题或凭据，不要直接入库或提交。
