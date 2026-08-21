# Day101 · 推理基准：量化、KV Cache 与容量决策

今天不把 FlashAttention、量化、KV Cache 当面试名词，而是用可复现指标做决策：质量先过
回归门槛，再看 TTFT、p95、输出吞吐、显存和成本。量化压缩模型权重；KV Cache 保存已算过
的注意力键值；二者解决的不是同一个瓶颈。

## 今日交付

- `benchmark.py`：p50/p95、TTFT、输出吞吐与 SLO gate。
- `docs/inference_decisions.md`：模型量化、FlashAttention、KV Cache 的决策边界。
- `tests/test_benchmark.py`：验证阈值失败会阻止发布。

## 今日边界

本地基准结果只在相同模型、提示长度、并发、硬件和版本下可比。不能把单请求速度当成
并发生产吞吐，也不能只因显存够就跳过质量评测。
