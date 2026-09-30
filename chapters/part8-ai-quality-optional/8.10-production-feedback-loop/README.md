# 8.10 线上反馈闭环：审查后再加入回归

[全书目录](../../README.md) · [上一章 8.9](../8.9-ci-layered-gate/README.md) · [下一章 9.1](../../part9-enterprise-infra-optional/9.1-intent-fewshot/README.md)

- **目标**：反馈先审查，再进入回归；线上数据不能自动污染生产行为。
- **前置**：8.9（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.10-production-feedback-loop`，进入 `.build/quality/8.10-production-feedback-loop/ai-testing` 后运行 `python -m pytest -q`

## 问题

用户点踩可能是答案错误，也可能是表达不喜欢或数据不足。不能把每次负反馈直接当标准答案，需要先审查再转成可执行案例。

## 概念

BadCase 保存候选失败；FeedbackQueue 负责去重（`case_id`）、审核状态和导出；回归样本还需要人工确认的预期结果，本章代码不记录预期，由审核者在导出后补写。反馈采集和改变生产行为是两个不同环节。

## 流程

1. 用户点踩：旗舰后端 `/feedback`（7.7 / step3）记录 `trace_id`、评分和原因；网页（7.8 / step3）的点踩按钮调用它。
2. 用 `trace_id` 从日志取回问题、回答和来源，组装成 `BadCase`（本章的测试直接构造，不实现这一步）。
3. `FeedbackQueue.submit` 入队，同一 `case_id` 只收一次；`review_queue()` 只列出待审核的负反馈。
4. 人工核对问题与来源，确认确实是系统错误后 `approve`。
5. `export_regression_cases` 只导出已批准的案例；其中 `answer` 是线上的出错回答，不是标准答案，审核者补上预期后才能写成断言。
6. 补全预期的案例进入回归集，由 8.9 的门禁保护后续修改。

```text
/feedback（7.7 / step3）→ BadCase → review_queue → 人工 approve → 导出 JSON → 补预期 → 回归集 / 8.9 门禁
```

## 衔接与新增

章节 8.9 的门禁只能阻止已知回归；章节 8.10 把线上负反馈变成新的已知回归：先进入人工审查队列，批准后导出为回归样本。

**本章新增**

| 文件 | 状态 | 作用 |
|---|---|---|
| `PROJECT_README.md` | 新增 | 总结 章节 8.1–8.10 的专项闭环和边界 |
| `src/ai_testing/feedback_loop.py` | 新增 | 去重、审查、批准和回归集导出 |
| `tests/test_feedback_loop.py` | 新增 | 验证负反馈队列和审核后导出 |

## 代码导读

feedback_loop.py 先读 BadCase，再读 FeedbackQueue 的接收、审核和导出逻辑，观察未审核数据能否进入回归。

实现文件：

- [feedback_loop.py](src/ai_testing/feedback_loop.py)

## 练习

构造一个重复点踩和一个预期不清的反馈，预测队列状态；完成审查后写出新增测试真正保护的行为。选做：给 `approve` 增加 `expected` 参数并写入导出结果，再补一个测试。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.10-production-feedback-loop
cd .build/quality/8.10-production-feedback-loop/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

教学队列未实现完整线上采集与数据治理；真实用户内容需按授权脱敏后使用。旗舰的 `Feedback` 只有 `trace_id`、评分和原因，转成 `BadCase` 需要日志里的问题与回答，本章没有实现这一步。

导出回归用例不等于已经修复问题；下一轮必须重新运行评测、确认指标改善，再把结果纳入发布证据。
