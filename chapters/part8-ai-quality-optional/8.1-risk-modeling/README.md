# 8.1 AI 测试策略：先找业务风险

[全书目录](../../README.md) · [下一章 8.2](../8.2-eval-data-engineering/README.md)

- **目标**：测试优先级必须由业务风险决定，而不是由模块数量决定。
- **前置**：第 3 篇、第 7 篇（测试对象是第 7 篇的最终后端）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.1-risk-modeling`，进入 `.build/quality/8.1-risk-modeling/ai-testing` 后运行 `python -m pytest -q`

## 问题

测试背景可以帮助我们识别AI系统的薄弱处，但首先要决定优先保护什么。答错商品介绍和泄露另一租户订单，影响不同，测试投入也应不同。

## 概念

风险由业务影响、发生可能与可发现性共同描述；风险矩阵把这些判断变成可讨论的排序，而不是按代码文件数量平均分配测试。

## 流程

1. 列出用户场景与潜在失败。
2. 用 Risk 保存各项判断。
3. RiskMatrix 汇总排序。
4. 把最高风险转换为具体验收场景。

```text
业务场景 → Risk(影响 × 发生可能性) → 优先级 → 测试覆盖缺口
```

## 衔接与新增

第 7 篇以浏览器前端（7.8 / step3）收尾；从章节 8.1 起进入可选的 AI 自动化测试专项。测试对象仍是同一个客服 Copilot（7.8 / step2 的后端），测试工具独立放在 `ai_testing` 包里，不混进业务代码。

**本章新增**

| 文件 | 作用 |
|---|---|
| `pyproject.toml` | 建立 章节 8.1–8.10 专项的可还原 Python 基线 |
| `src/ai_testing/risk.py` | 风险登记、评分、分级和测试覆盖检查 |
| `tests/test_risk.py` | 验证风险排序、重复登记和覆盖缺口 |

## 代码导读

risk.py 先读 Risk 的字段，再读 RiskMatrix 的排序逻辑，对照测试中的边界风险。

实现文件：

- [risk.py](src/ai_testing/risk.py)

## 练习

为退款误答、跨用户订单和流式断连各写一条风险，解释评分依据，再检查最高项是否已有测试。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.1-risk-modeling
cd .build/quality/8.1-risk-modeling/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

本篇是独立测试工具累积线，评分是业务判断的记录，不是对真实事故概率的统计估计。

风险矩阵只能决定“先测什么”，不能证明功能已经正确；下一章会把风险中的业务场景转成可执行评测数据。
