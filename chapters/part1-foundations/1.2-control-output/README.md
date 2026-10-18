# L1.2 输出控制 · Gate（原 1.2）

[全书目录](../../README.md) · [上一章 1.1](../1.1-first-call/README.md) · [下一章 1.3](../1.3-structured-output/README.md)

- **能力**：构造可验证的请求参数；收集流式片段并处理空流、坏片段、超时和中断。
- **v2 路径**：L1.2 / 核心（Gate；输出控制）
- **前置**：1.1（一次调用）。
- **时间盒**：4 小时（1h 读 + 2h 实现 + 1h 故障分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `control_output.py`。
- **验收命令**：

```bash
python chapters/part1-foundations/1.2-control-output/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

`temperature` 和 `stream` 看起来只是两个参数，但生产里会出这些事：

- 温度或 `max_tokens` 传错，成本/行为不可控；
- 流式返回空流，前端一直转圈；
- 某个片段不是字符串，拼接时崩；
- 流到一半上游断了，已经显示的内容怎么办；
- 用户等待首 token 太久，体验崩。

这个 gate 把“控制输出”拆成 **请求参数 + 流式收集 + 失败出口**，用假流注入这些故障。

## 任务

实现 `gate/starter.py` 的三个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `build_request` | 校验 temperature、max_tokens、stop；返回规范化 dict |
| `collect_stream` | 拼接片段；记录片段数、首片段毫秒；处理空流/坏片段/中断 |
| `stream_text` | 把 request 原样交给 `chat_fn`；处理超时/异常；调用 `collect_stream` |

关键口径：

- `temperature` 必须在 `0–2`（含端点）；`max_tokens` 是 `1–8192` 的整数；`stop` 最多 4 个非空字符串。
- 空流：`error="empty_stream"`，`text=""`，`chunks=0`，`first_chunk_ms=-1`。
- 片段不是 `str`：`error="bad_chunk"`，保留此前已拼接内容。
- 迭代抛异常：`error="model_error"`，保留已收到内容。
- `chat_fn` 超时：`error="timeout"`；其他异常：`error="model_error"`。
- `chat_fn(request)` 只能调用一次，`request` 必须原样传入。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | `temperature=-0.1` / `2.1` | `RequestError` |
| 2 | `max_tokens=0` / `9000` / `True` | `RequestError` |
| 3 | `stop="x"` / `[""]` / 5 个元素 | `RequestError` |
| 4 | 空流 | `empty_stream` |
| 5 | 片段里混入 `123` | `bad_chunk`，保留前面的文本 |
| 6 | 迭代到一半抛异常 | `model_error`，保留已收文本 |
| 7 | `chat_fn` 抛 `TimeoutError` | `timeout` |
| 8 | `chat_fn` 抛 `RuntimeError` | `model_error` |

## 验收标准

`gate_check.py` 的 10 项全部 PASS：

- 默认/自定义参数；8 类非法参数。
- 正常流、空流、坏片段、迭代异常。
- request 原样传入；流式超时/异常。

通过后，在 [workbook.md](workbook.md) 写：

1. 首 token 延迟为什么要单独记录，而不是只看总耗时？
2. 流中断时已经显示的内容应该保留还是丢弃？两种选择的代价是什么？
3. `temperature=0` 为什么仍不能保证完全可复现？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（10/10）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 1.2
```

对照时只回答：

1. 参考实现只改了 `temperature`，没有校验参数；上生产要先补哪一层？
2. `chain.stream` 的每个 chunk 是什么类型？和本 gate 的 `collect_stream` 输入是否一致？
3. 参考实现没有处理流中断；如果网络断了，用户会看到什么？

## 概念地图

- **采样参数**：temperature 控制随机性，不保证事实正确；评测要固定它。
- **max_tokens**：成本与截断边界；不是越大越好。
- **stop**：提前停止条件；要限制数量和内容，避免误停。
- **流式**：首 token 延迟、片段顺序、中断处理，都是用户体验的一部分。
- **可复现**：temperature=0 提高稳定性，但模型版本/服务端实现仍可能带来差异。

## 边界

- gate 用假流，不验证真实模型输出质量。
- 通过 gate 只证明参数与流式收集结构正确，不证明回答正确。
- 真实前端展示、SSE 和断线重连在 L5.1/L8.7 展开。
