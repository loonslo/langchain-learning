# L4.5 扩展：规划与执行 · Gate（原 4.8）

[全书目录](../../README.md) · [上一章 4.7](../4.7-structured-routing/README.md) · [下一章 4.9](../4.9-observability/README.md)

- **能力**：把模型输出解析成有界计划；逐步执行；计划/执行异常有出口；超长截断。
- **v2 路径**：L4.5 / 核心（Gate；规划与执行）
- **前置**：4.5（ReAct）、4.7（结构化路由）。
- **时间盒**：6 小时（1h 读 + 4h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `plan_and_execute.py`。
- **验收命令**：

```bash
python chapters/part4-agents-langgraph/4.8-plan-and-execute/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

Plan-and-Execute 的失败模式很集中：

- 模型输出编号/空行/重复步骤，直接当计划；
- 计划 1 步或 20 步，没有上下界；
- 计划生成失败/执行某步失败，整条链路崩；
- 计划超长，cursor 越界；
- 执行结果和计划对不上，审计困难。

这个 gate 用脚本化 planner/executor，验证解析、边界、异常和截断。

## 任务

实现 `gate/starter.py` 的两个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `parse_plan` | 去编号/空行/重复；步数在 [min,max]；非法报错 |
| `run_plan` | 规划 → 逐步执行；异常/超长有出口；结果与计划对应 |

关键口径：

- `parse_plan` 默认 2–4 步；越界/非字符串 -> `ValueError`。
- 空任务、`max_steps < 1` -> `ValueError`。
- `plan_fn` 异常 -> `error="plan_error"`；`execute_fn` 异常 -> `error="execute_error"`。
- 计划超过 `max_steps` -> 只执行前 max_steps 步，`error="plan_too_long"`。
- 正常 `results` 与 `plan` 等长，`error=None`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 带编号/重复的计划 | 去编号、去重、保序 |
| 2 | 1 步或 5 步 | `ValueError` |
| 3 | 非字符串计划输出 | `ValueError` |
| 4 | planner 抛异常 | `plan_error` |
| 5 | executor 抛异常 | `execute_error` |
| 6 | 3 步计划，max_steps=2 | 执行 2 步，`plan_too_long` |
| 7 | max_steps=0 | `ValueError` |

## 验收标准

`gate_check.py` 的 6 项全部 PASS：

- 计划解析、步数/类型校验、正常执行、计划/执行异常、超长截断、max_steps 校验。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么计划要有步数上下界？
2. 计划错了和某步执行错了，修复策略有什么不同？
3. `plan_too_long` 应该截断还是拒绝？两种选择的代价？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（6/6）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 4.8
```

对照时只回答：

1. 参考实现的 `planner` 怎么解析步骤？有没有步数上下界？
2. 参考实现的 `executor` 用 `cursor` 推进；它怎么判断结束？
3. 参考实现没有 replan；计划错了会怎样？

## 概念地图

- **Plan-and-Execute**：先规划、再按游标执行。
- **显式计划**：计划是状态，可审计、可恢复。
- **有界**：步数上下界；超长截断/拒绝。
- **失败出口**：plan_error / execute_error / plan_too_long。
- **replan**：计划错了重新规划；本 gate 不覆盖。

## 边界

- gate 用脚本化 planner/executor，不调用真实模型。
- 通过 gate 只证明解析/执行结构正确，不证明计划质量。
- 真实 planner/executor、replan 见参考实现与后续。
