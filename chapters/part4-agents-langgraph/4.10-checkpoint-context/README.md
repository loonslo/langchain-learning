# L4.6 扩展：检查点与上下文 · Gate（原 4.10）

[全书目录](../../README.md) · [上一章 4.9](../4.9-observability/README.md) · [下一章 4.11](../4.11-streaming-hitl/README.md)

- **能力**：按 thread_id 保存/读取状态快照；隔离会话；按条数裁剪上下文并保留 system。
- **v2 路径**：L4.6 / 核心（Gate；检查点与上下文）
- **前置**：4.9（可观测性）、1.4（会话记忆）。
- **时间盒**：6 小时（1h 读 + 4h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `checkpoint_context.py`。
- **验收命令**：

```bash
python chapters/part4-agents-langgraph/4.10-checkpoint-context/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

没有检查点，图跑完 state 就没了；有了检查点，又容易出现：

- 不同用户共享状态；
- 保存的是外部引用，后续修改污染快照；
- 裁剪把 system 删了，模型行为漂移；
- 裁剪修改原列表；
- 空 thread_id/非法 max_items 不报错。

这个 gate 用内存 store 和消息列表，验证隔离、副本和裁剪边界。

## 任务

实现 `gate/starter.py` 的 `CheckpointStore` 和 `trim_history`：

| 接口 | 你要交付的行为 |
|---|---|
| `save` | 保存副本；空 thread_id -> `ValueError` |
| `load` | 返回副本；不存在 -> None |
| `clear` | 删除；不存在不报错 |
| `trim_history` | 保留 system + 最近 N；不改输入；max<1 报错 |

关键口径：

- 保存/读取都用副本，不持有外部引用。
- `thread_id` 隔离；`load` 缺失返回 None。
- `keep_system=True` 且首条是 system：保留它 + 最近 `max_items-1` 条。
- 没有 system 或 `keep_system=False`：保留最近 `max_items` 条。
- `max_items` 大于长度：返回全部。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | save/load/clear | 读写正确，clear 后 None |
| 2 | t1/t2 两会话 | 互不影响 |
| 3 | 修改外部 state | 快照不变 |
| 4 | system + 5 条，max=3 | system + 最近 2 条 |
| 5 | 无 system，max=2 | 最近 2 条 |
| 6 | max=0 / 检查输入 | `ValueError` / 未修改 |

## 验收标准

`gate_check.py` 的 6 项全部 PASS：

- 保存/读取/清除、会话隔离、副本、system 裁剪、无 system/长度不足、非法参数/不改输入。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么保存/读取都要用副本？
2. 裁剪时为什么优先保留 system？
3. 裁剪丢信息和摘要保事实，怎么选？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（6/6）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 4.10
```

对照时只回答：

1. 参考实现用 `InMemorySaver` 按 `thread_id` 存快照；你的 store 和它对应关系是什么？
2. 参考实现的 `trim_messages` 按 token 预算，你的按条数；差别在哪？
3. 摘要节点为什么需要额外一次模型调用？

## 概念地图

- **checkpoint**：每步保存 state 快照，按 thread_id 隔离。
- **多轮记忆**：同一 thread 续聊带历史。
- **中断恢复**：从上次快照继续；有副作用工具要幂等。
- **上下文裁剪**：按条数/token 保留最近；system 优先。
- **摘要**：压缩旧历史，保事实但多一次调用。

## 边界

- gate 用内存 store，不验证 LangGraph checkpointer/Sqlite/Postgres。
- 通过 gate 只证明隔离/副本/裁剪结构正确。
- 真实记忆、摘要质量、恢复副作用见参考实现与 4.11。
