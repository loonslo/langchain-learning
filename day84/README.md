# Day84 · LLM-as-Judge 校准

> 今天解决：Judge 给出了漂亮分数，但没人证明它和人工判断一致。
>
> 第一性原则：Judge 是测量工具，必须先校准，不能把模型分数直接当真值。

## 与 Day83 的文件衔接

Day83 发现召回、引用和生成质量需要分层；Day84 用人工标签校准 Judge 阈值，避免自动评测把系统性误判放大到 CI。

### 今天新增

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/judge.py` | 新增 | 阈值搜索、agreement、Cohen's kappa 和混淆矩阵 |
| `tests/test_judge.py` | 新增 | 验证最佳阈值和空校准集 |

## 真实调用链

```text
人工标签 + Judge score → calibrate → threshold/kappa → 是否采信自动分数
```

## 验收

```bash
python tools/materialize_ai_testing_day.py 84
cd .build/day84/ai-testing
python -m pytest -q
```

## 今日边界

校准样本过少或分布单一时，kappa 仍可能不稳定；报告必须保存样本来源和版本。
