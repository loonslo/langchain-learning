# L5.2 可靠性 · Gate（原 5.2）

[全书目录](../../README.md) · [上一章 5.1](../5.1-serve-fastapi/README.md) · [下一章 5.3](../5.3-cost-cache-routing/README.md)

- **能力**：生成指数退避序列；区分可重试/不可重试错误；按 usage 估算成本。
- **v2 路径**：L5.1 / 核心（Gate；可靠性/退避/成本）
- **前置**：5.1 的 gate（最小超时/重试）、1.1、2.6。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `reliability.py`。
- **验收命令**：

```bash
python chapters/part5-production/5.2-reliability-retry/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

重试和成本统计最容易出这些错：

- 无差别重试，参数错/权限错也重试；
- 退避没有上限，等待时间爆炸；
- 没有 jitter，客户端同步重试打爆服务；
- `max_retries` 含义混淆（次数 vs 总尝试）；
- 成本公式除错 1000/1000000，或 usage 缺失时崩。

这个 gate 用纯函数验证退避、可重试和成本公式，不调用模型。

## 任务

实现 `gate/starter.py` 的三个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `backoff_delays` | base,2base,4base...，每项截断到 max_delay；参数校验 |
| `is_retryable` | 只把 TimeoutError/ConnectionError 判为可重试 |
| `estimate_cost` | total_tokens/1000*单价；缺失/None -> 0；负单价报错 |

关键口径：

- `max_retries=0` -> []；负数/base<=0/max_delay<=0 -> `ValueError`。
- 退避序列长度等于 max_retries，每项 `min(base*2^i, max_delay)`。
- ValueError/KeyError/PermissionError 不可重试。
- 成本保留浮点，不四舍五入。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | max_retries=3 | [1,2,4] |
| 2 | 6 次，max_delay=20 | [1,2,4,8,16,20] |
| 3 | 0 次 / 负数 | [] / `ValueError` |
| 4 | base=0 / max_delay=0 | `ValueError` |
| 5 | Timeout/Connection/ValueError | True/True/False |
| 6 | 2000 tokens，0.001 | 0.002 |
| 7 | None/空 usage | 0.0 |
| 8 | 负单价 | `ValueError` |

## 验收标准

`gate_check.py` 的 5 项全部 PASS：

- 指数退避、参数校验、可重试、成本、成本参数。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么“参数错误”不该重试？
2. 退避为什么要有上限和 jitter？
3. 成本公式里最容易写错的是什么？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（5/5）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 5.2
```

对照时只回答：

1. 参考实现的 `invoke_with_retry` 有两个什么坑？
2. `get_reliable_llm` 怎么解决这两个坑？
3. `usage_metadata` 里哪个字段用于成本？

## 概念地图

- **超时**：单次调用上限。
- **指数退避**：1/2/4…，加 jitter 防同步风暴。
- **可重试**：瞬时错误才重试；确定性错误快速失败。
- **成本**：tokens/1000*单价；usage 缺失要能降级。
- **缓存边界**：评测可缓存；生产问答要防过期/失效。

## 边界

- gate 用纯函数，不调用真实模型/缓存。
- 通过 gate 只证明退避/重试/成本逻辑正确。
- 真实限流、主备切换、缓存失效见参考实现。
