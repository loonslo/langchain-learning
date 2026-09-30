# 3.7 回归曲线：看见改动带来的收益与退化

[全书目录](../../README.md) · [上一章 3.6](../3.6-langsmith-eval/README.md) · [下一章 3.8](../3.8-prompt-ab-judge/README.md)

- **目标**：在同一批问题上比较基线版与候选版的质量、延迟和错误率，找出回归。
- **前置**：2.6；3.5（生成 `eval_set_full.json`）；`DEEPSEEK_API_KEY`；本地 embedding 模型。
- **环境**：调用真实模型；`LANGSMITH_API_KEY` 可选。
- **命令**：`python tools/run_chapter.py 3.7 --no-upload`

## 问题

一次改动提高了平均分，却让某类问题全部答错，总分会掩盖这个问题。回归对比固定问题，在基线版和候选版上分别运行，既看整体趋势，也保留每条退化样本。

## 概念

- **基线与候选**：基线是比较起点；候选是待评估的变更。本章的基线是稳定版 RAG（`temperature=0`，要求依据上下文并标来源），候选放松了来源和拒答要求，用来暴露回归风险。
- **可比较**：只有资料、题集、指标和配置都相同，两条曲线才有解释价值。
- **指标**：`keyword_score`、`citation_score`、`refusal_ok`，以及三者组合的 `pass_rate`；延迟用 P50/P99；`Error Rate` 只统计运行时异常，回答质量差不算。
- **门禁**：通过率下降超过 2%、引用分下降超过 2%、拒答正确率下降、错误率上升或 P99 延迟增加超过 2 秒时，判定为回归。

## 流程

1. `load_rag_cases` 读取 `eval_set_full.json`，把题型名转换成本章使用的名字。
2. 用同一套评测集，分别运行 baseline 与 candidate 的真实 RAG 链，记录答案与耗时。
3. `score_one` 计算每条样本的三项分数与是否通过；`local_summary` 汇总成指标。
4. `regression_alerts` 比较两版，输出回归判断；加 `--fail-on-regression` 时，回归会让程序以错误退出。
5. 配置了 `LANGSMITH_API_KEY` 且未加 `--no-upload` 时，同时上传两组 experiment。
6. 加 `--write-failures` 时，把 candidate 的失败样本写入 `chapters/shared-data/failures.json`，供 3.10 诊断。

## 代码导读

[regression_curve.py](regression_curve.py)：先看 `load_rag_cases` 与两个链（`baseline_chain`、`candidate_chain`）的差别，再看 `score_one` 与 `regression_alerts`，最后看 `main` 里的命令行参数。

## 练习

1. 运行 `python tools/run_chapter.py 3.7 --no-upload`，找出候选版比基线差在哪些题、哪个指标。
2. 加 `--write-failures`，打开生成的 `failures.json`，看失败记录里包含哪些字段。
3. 只改变候选版的一个参数（如 `temperature`），预测哪些题可能受影响，再检查逐题差异。

## 运行与边界

- 每条样本要真实调用模型两次，25 条共 50 次，会产生费用。
- 25 条样本的通过率波动很大，一两条的变化不能当作统计结论。
- 候选版的“回归”是故意设计出来的，用于演示；真实项目里要检查评测集是否有代表性。
