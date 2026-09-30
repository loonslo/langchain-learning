# 8.5 Judge 校准：先证明测量工具可信

[全书目录](../../README.md) · [上一章 8.4](../8.4-rag-layered-testing/README.md) · [下一章 8.6](../8.6-agent-trajectory-testing/README.md)

- **目标**：Judge 是测量工具，必须先校准，不能把模型分数直接当真值。
- **前置**：8.4（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.5-judge-calibration`，进入 `.build/quality/8.5-judge-calibration/ai-testing` 后运行 `python -m pytest -q`

## 问题

如果评委总给高分，CI 可能稳定放过错误答案。把评委结果与人工标签对照，找出阈值和系统偏差，才能决定哪些结论可以自动使用。

## 概念

人工标签是校准参照；阈值把分数变成通过或失败；`calibrate` 在候选阈值里选与人工标签一致率最高的（并列取较小阈值），同时给出 Cohen's kappa（扣除“靠运气也会一致”的部分）和混淆矩阵；人工标签和 Judge 输出全为同一类时 kappa 没有意义。不同类别的误报与漏报代价要分开看。

## 流程

1. 收集人工标签和评委分数。
2. labels_at 应用候选阈值。
3. calibrate 汇总对照。
4. 查看 CalibrationReport 后决定使用范围。

```text
人工标签 + Judge score → calibrate → threshold/kappa → 是否采信自动分数
```

## 衔接与新增

章节 8.4 发现召回、引用和生成质量需要分层；章节 8.5 用人工标签校准 Judge 阈值，避免自动评测把系统性误判放大到 CI。

**本章新增**

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/judge.py` | 新增 | 阈值搜索、agreement、Cohen's kappa 和混淆矩阵 |
| `tests/test_judge.py` | 新增 | 验证最佳阈值和空校准集 |

## 代码导读

judge.py 先读 JudgeExample，再读 labels_at、calibrate 和一致性计算，核对样本不足或分布偏斜的情况。

实现文件：

- [judge.py](src/ai_testing/judge.py)

## 练习

让几条明显错误答案得到高分，观察校准报告；再移动阈值，记录误报与漏报怎样变化。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.5-judge-calibration
cd .build/quality/8.5-judge-calibration/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

合成分数验证校准算法，不能证明真实模型评委可靠；人工分歧和领域变化需要持续检查。

校准样本过少或分布单一时，kappa 仍可能不稳定；报告必须保存样本来源和版本。
