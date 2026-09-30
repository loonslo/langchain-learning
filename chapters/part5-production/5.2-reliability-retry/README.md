# 5.2 超时、重试与成本统计：可靠也要有预算

[全书目录](../../README.md) · [上一章 5.1](../5.1-serve-fastapi/README.md) · [下一章 5.3](../5.3-cost-cache-routing/README.md)

- **目标**：给模型调用加上超时和重试，并能算清每次调用的 token 和成本。
- **前置**：1.1、2.6；`DEEPSEEK_API_KEY`。
- **环境**：调用真实模型。
- **命令**：`python tools/run_chapter.py 5.2`

## 问题

LLM 调用会超时、被限流、偶发失败。上线前必须加防护，还要能回答“每次调用花了多少 token、多少钱”。

## 概念

- **超时**：别让一次卡住的调用拖垮整个服务。
- **指数退避重试**：失败后等 1 秒、2 秒、4 秒再试。手写版只为理解原理，有两个生产不能接受的坑：无差别重试（参数错误、鉴权失败重试也没用），没有随机抖动 jitter（大量客户端同时退避，会引发同步重试风暴）。
- **生产做法**：`common.get_reliable_llm()`（超时 + `with_retry` + jitter + 可选备用模型），capstone 的问答链真实在用它。只重试瞬时故障，别吞异常。
- **缓存**：只演示适用边界：评测和开发场景可以缓存以省钱；生产问答链路不接入（原因见代码注释）。
- **token 与成本**：返回消息的 `usage_metadata` 里有 `input_tokens`、`output_tokens`、`total_tokens`，乘以单价即可粗算成本。

## 流程

1. `invoke_with_retry`：手写指数退避重试（对照组）。
2. 直接使用 `common.get_reliable_llm()`：生产版。
3. `build_tenacity_llm`：用 tenacity 做更精细的控制（了解即可）。
4. `enable_eval_cache`：开启 SQLite 缓存，对比首次调用与命中缓存的耗时。
5. 读取 `usage_metadata`，按占位单价粗算成本。

## 代码导读

[reliability.py](reliability.py)：先看 `invoke_with_retry` 的注释里列出的两个坑，再看 `get_reliable_llm` 怎样解决它们（在 `common.py` 里）。

## 练习

1. 断开网络或把超时设得很小，观察手写重试版的日志和最终报错。
2. 说明为什么“参数错误”不该重试，而“429 限流”应该重试。
3. 把占位单价换成你所用模型的真实价格，算一算 1000 次调用的成本。

## 运行与边界

- 会调用真实模型并产生费用；缓存演示会在本章目录写 `.llm_cache.db`（已被 `.gitignore` 忽略）。
- 重试只适用于幂等或只读的操作；有副作用的写操作需要幂等键，见 7.4。
- 备用模型只能应对同一供应商的单个模型故障，不能解决整个供应商的故障。
