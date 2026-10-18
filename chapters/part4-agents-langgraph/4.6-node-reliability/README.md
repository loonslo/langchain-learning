# L4.3 扩展：节点可靠性 · Gate（原 4.6）

[全书目录](../../README.md) · [上一章 4.5](../4.5-react-agent/README.md) · [下一章 4.7](../4.7-structured-routing/README.md)

- **能力**：节点失败降级；区分可重试/不可重试错误；给慢调用设真实超时。
- **v2 路径**：L4.3 / 核心（Gate；节点可靠性）
- **前置**：4.5（ReAct 工具循环）。
- **时间盒**：6 小时（1h 读 + 4h 实现 + 1h 故障分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `node_reliability.py`。
- **验收命令**：

```bash
python chapters/part4-agents-langgraph/4.6-node-reliability/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

默认情况下，节点一抛异常整张图就崩，用户拿到 500。生产必须区分：

- 哪些错误值得重试（超时/连接断开）；
- 哪些错误重试也没用（参数错/权限错）；
- 慢调用怎么真正限时，而不是“跑完再看耗时”；
- 降级结果怎么让用户知道，而不是伪装成真实数据。

这个 gate 用假函数/真 sleep，验证降级、可重试判断和真实超时。

## 任务

实现 `gate/starter.py` 的三个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `robust_call` | 成功返回 ok；异常返回 fallback + error，不向外抛 |
| `is_retryable` | 只把 TimeoutError/ConnectionError 判为可重试 |
| `with_timeout` | 真正限时；超时返回 on_timeout；fn 异常透传 |

关键口径：

- `robust_call` 的 `error` 是可读原因，`value=fallback`。
- `ValueError/KeyError` 不可重试。
- `seconds <= 0` -> `ValueError`。
- 超时不能无限等待；`fn` 自身异常不能被当成“超时”吞掉。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | fn 成功 | ok=True，原值 |
| 2 | fn 抛 ConnectionError | ok=False，fallback，error 含原因 |
| 3 | Timeout/Connection vs ValueError/KeyError | True / False |
| 4 | 快速 fn + 1s | 原值 |
| 5 | sleep 0.1 + 0.02s | 0.02s 左右返回 fallback |
| 6 | seconds=0/-1 | `ValueError` |
| 7 | fn 抛 ValueError | 原样抛出 |

## 验收标准

`gate_check.py` 的 7 项全部 PASS：

- 成功、降级、可重试、快速、超时、非法 seconds、异常透传。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么“参数错误”不该重试？
2. 降级结果为什么必须让用户/下游知道？
3. “跑完再看耗时”和真正超时的差别是什么？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（7/7）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 4.6
```

对照时只回答：

1. 参考实现的 `robust_node` 捕获哪些异常？会不会吞掉编程错误？
2. 参考实现的 `with_timeout` 是真超时还是“跑完再看”？
3. `RetryPolicy` 的 `retry_on` 为什么只列 Timeout/Connection？

## 概念地图

- **降级**：失败返回可用结果，图继续；但要标注“降级”。
- **可重试**：瞬时错误才重试；确定性错误快速失败。
- **超时**：必须能中断等待，不是事后统计。
- **幂等**：重试只适用于只读/幂等操作；写操作要幂等键。
- **可观测**：降级/重试要记录原因，见 4.9。

## 边界

- gate 用假函数/真 sleep，不验证 RetryPolicy/ToolNode 真实行为。
- 通过 gate 只证明降级/超时结构正确。
- 真实模型限流、工具异常回喂见参考实现与 4.9。
