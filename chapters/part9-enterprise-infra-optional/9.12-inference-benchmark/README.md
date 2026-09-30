# 9.12 推理基准：先过质量，再比较容量

[全书目录](../../README.md) · [上一章 9.11](../9.11-vllm-gpu/README.md) · [下一章 10.1](../../part10-mcp-a2a-optional/10.1-mcp-auth-approval/README.md)

- **目标**：用可复现指标做推理决策：质量先过回归门槛，再比较 TTFT、p95、输出吞吐、显存和成本。
- **前置**：9.11（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.12-inference-benchmark`，进入 `.build/enterprise/9.12-inference-benchmark/enterprise-support` 后运行 `python -m pytest -q`

## 问题

量化后速度可能更快，但若业务答案退化，性能提升并不能直接换成发布结论。我们把质量、首字延迟、整体延迟和吞吐放在同一决策过程里。

## 概念

TTFT 是首字等待；输出吞吐描述生成速度，这里按成功请求的输出 token 总数 ÷ 延迟总和计算（相当于串行执行，并发压测时会低估，应另用墙钟时间）；p95 描述较慢请求；量化压缩模型权重，KV Cache 保存已算过的注意力键值，二者影响的是不同资源。不同配置比较需要相同工作负载。

## 流程

1. 采集 RequestSample。
2. summarize 汇总延迟和吞吐。
3. 按 InferenceSlo 执行 release_errors。
4. 结合质量回归决定是否继续。

## 本章交付

- `benchmark.py`：p50/p95、TTFT、输出吞吐与 SLO gate。
- `docs/inference_decisions.md`：模型量化、FlashAttention、KV Cache 的决策边界。
- `tests/test_benchmark.py`：验证阈值失败会阻止发布。

## 代码导读

benchmark.py 先读样本字段与统计方法，再看发布错误；本章决策文档说明测量范围和不可夸大的结论。

实现文件：

- [benchmark.py](src/enterprise_support/benchmark.py)

## 练习

用合成样本比较平均值与 p95，再加入质量失败条件，解释为何最快配置也可能不允许发布。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.12-inference-benchmark
cd .build/enterprise/9.12-inference-benchmark/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

离线统计验证指标实现，不代表真实 GPU、量化或容量已经测得；硬件结论需实际实验。

本地基准结果只在相同模型、提示长度、并发、硬件和版本下可比。不能把单请求速度当成并发生产吞吐，也不能只因显存够就跳过质量评测。
