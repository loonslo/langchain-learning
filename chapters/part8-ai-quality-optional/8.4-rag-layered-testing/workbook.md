# L3.1 扩展：RAG 分层检索评测 · Gate 记录

任务书见 [README](README.md)。先预测，再实现，最后填结果；通过 gate 之前不要打开 `src/ai_testing/rag_eval.py`。

## Gate 结果

- 首次运行：x / 6
- FAIL 项与修正：待填写
- 最终：6 / 6
- `gate_report.json`：待填写

## 解释

1. recall 和 precision 分别暴露什么问题？
2. 拒答样本为什么要单独看？
3. MRR 为什么比 recall 更关心排序？

## 未验证边界

- 不调用模型，只算指标。
- 真实索引/数据未验证。
