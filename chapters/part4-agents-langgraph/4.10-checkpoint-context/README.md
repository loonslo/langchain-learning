# 4.10 检查点与上下文：恢复流程和管理对话

[全书目录](../../README.md) · [上一章 4.9](../4.9-observability/README.md) · [下一章 4.11](../4.11-streaming-hitl/README.md)

- **目标**：用检查点（checkpoint）保存图状态，实现多轮记忆和中断恢复；并管理不断变长的上下文。
- **前置**：4.9、1.4。
- **环境**：调用真实模型；摘要部分需要 `langmem`（`pip install langmem`）。
- **命令**：`python tools/run_chapter.py 4.10`

## 问题

前面的图每次 `invoke` 跑完，state 就没了，等于没有记忆。另一方面，对话越长，messages 越多，迟早超出窗口，也越来越贵。

## 概念

- **状态持久化（checkpoint）**：checkpointer 在每一步自动保存 state 快照，按 `thread_id` 隔离会话。带来三件事：多轮记忆（同一 `thread_id` 续聊自动带上历史，不必手拼 messages）；中断恢复（挂了或被打断后从上次的检查点接着运行，4.11 的人工介入就靠它）；多用户隔离（不同 `thread_id` 各记各的）。
- **`InMemorySaver`** 存在内存里，重启即丢；生产换 `SqliteSaver`、`PostgresSaver` 落盘。
- **上下文管理**：常见策略是只留最近 N 轮，把更早的压成摘要。裁剪（`trim_messages`）免费但会丢信息；摘要（`langmem` 的 `SummarizationNode`）要多花一次模型调用，但能保住事实。历史里有“必须记住的事实”（名字、决定）就用摘要。
- **完整历史与喂给模型的视图分离**：checkpointer 保存全量 messages，模型只看压缩后的版本，审计和回放不丢数据。

## 流程

`checkpoint_context.py`：

1. `demo_memory`：同一 `thread_id` 多轮记忆；换 `thread_id` 互不影响。
2. `demo_trim`：按 token 上限裁剪历史。
3. `demo_context` / `build_summary_app`：历史超过阈值后自动摘要，观察早先的事实（如名字）是否还在。

## 代码导读

[checkpoint_context.py](checkpoint_context.py)：先看 `build_app` 里 `compile(checkpointer=...)`，再看 `demo_memory` 里 `thread_id` 的用法，最后看摘要节点的阈值参数。

## 练习

1. 把 `InMemorySaver` 换成 `SqliteSaver`，重启进程后验证记忆仍在。
2. 把 `max_tokens_before_summary` 调小到 64，看第 2 轮就触发摘要后，“小王”还在不在。
3. 用两个不同的 `thread_id` 各聊几句，验证记忆互不影响。

## 运行与边界

- 调用真实模型并产生费用；摘要本身也是一次模型调用，可能丢细节。
- 有副作用的工具在恢复时可能被重复触发，需要幂等性；检查点不保证外部操作只执行一次。
