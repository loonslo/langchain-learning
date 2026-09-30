# 3.8 提示词 A/B 对比：用固定问题检验修改

[全书目录](../../README.md) · [上一章 3.7](../3.7-eval-regression-curve/README.md) · [下一章 3.9](../3.9-agent-trajectory-eval/README.md)

- **目标**：用 LangSmith 对两版 prompt 做 A/B 对比，并校验 LLM 裁判与人工打分是否一致。
- **前置**：3.6、3.7；`LANGSMITH_API_KEY` 和 `DEEPSEEK_API_KEY`。
- **环境**：调用真实模型并上传 LangSmith。
- **命令**：`python tools/run_chapter.py 3.8`

## 问题

选提示词不该靠“我觉得顺眼”。同一批问题、两版提示词、同一套指标，才能用数据比较。而当指标里含有 LLM 裁判时，还要证明裁判可信，否则它的分数没有意义。

## 概念

- **prompt A/B**：在同一个评测集上，用两版提示词分别回答，比较关键词、来源、拒答和裁判分数。本章的两版是 `strict`（简短、必须带来源、信息不足就直接拒答）和 `helpful`（可补充背景，解释更完整）。
- **LLM-as-judge 一致性**：裁判也会错，所以拿人工打分做校验。`judge_human_agreement` 比较裁判“通过/不通过”与人工标签，低于 0.7 要警惕。
- **dataset 与 experiment**：dataset 是考题本（问题 + 参考答案 + 人工分）；experiment 是在它上面跑一遍并生成指标；同一 dataset 跑两次 experiment，就能在 LangSmith 里对比 A/B。
- **普通与汇总评估器**：普通评估器对每条样本运行一次；汇总评估器对整个 experiment 运行一次（如 `prompt_pass_rate`）。

## 流程

1. `require_api_keys` 检查密钥。
2. `ensure_langsmith_dataset` 创建或补齐 dataset（14 条用例，含参考答案、关键词、期望来源、是否应拒答、人工分）。
3. 分别对 `strict`、`helpful` 运行 experiment：知识库检索（`retrieve_docs`）→ 提示词链 → 四个评估器（`keyword_score`、`citation_score`、`refusal_alignment`、`llm_judge`）+ 两个汇总评估器。
4. 把两个 experiment 的链接写入本章 `reports/prompt_ab_judge_agreement.json`。

## 代码导读

本文件较长（约 740 行），但大部分是数据和评估函数。按下面的顺序读：

1. 知识库 `KNOWLEDGE_BASE` 和用例 `PROMPT_AB_CASES`（每条用例注释了理论上哪版更占优）。
2. `build_prompt_chain`：两版提示词的差异，是本章 A/B 的核心。
3. 评分函数：`keyword_score`、`citation_score`、`refusal_alignment`，再到 `judge_answer` / `llm_judge`。
4. `ensure_langsmith_dataset`、`run_experiment`、`main`：怎样把以上内容接到 LangSmith。

## 练习

1. 运行后在 LangSmith 里对比两个 experiment：哪版通过率更高？是否符合用例注释里的预期？
2. 查看 `judge_human_agreement`。如果低于 0.7，找出裁判和人工分歧最大的样本。
3. 增加一条“问法刁钻”的用例，先预测哪版更占优。

## 运行与边界

- 会调用真实模型并把数据上传到 LangSmith，产生费用；本章自带一个小型硬编码知识库，不依赖其他章节的文件。
- 本地只保存 experiment 的链接摘要，真实结果在 LangSmith 网页里查看。
- 14 条样本的差异不足以下统计结论。
