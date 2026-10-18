# L3.6 扩展：Prompt A/B 指标 · Gate 记录

任务书见 [README](README.md)。先预测，再实现，最后填结果；通过 gate 之前不要打开 `prompt_ab_judge.py`。

## Gate 结果

- 首次运行：x / 5
- FAIL 项与修正：待填写
- 最终：5 / 5
- `gate_report.json`：待填写

## 解释

1. 指标为什么要归一化后再匹配？
2. 无关键词/无来源为什么记 1.0？
3. 误拒答为什么要单独扣分？

## 未验证边界

- 不调用模型/LangSmith，只算指标。
- 真实 A/B 结论未验证。
