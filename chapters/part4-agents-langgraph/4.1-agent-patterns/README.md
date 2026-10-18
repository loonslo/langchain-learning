# L4.1 Agent 模式 · Gate（原 4.1）

[全书目录](../../README.md) · [上一章 3.10](../../part3-evals/3.10-eval-report-failures/README.md) · [下一章 4.2](../4.2-langgraph-basics/README.md)

- **能力**：区分固定工作流与动态循环；用状态/节点/条件边搭一个有界、失败有出口的 Agent 循环。
- **v2 路径**：L4.1 / 核心（Gate；Agent 模式）
- **前置**：1.5（工具调用）。
- **时间盒**：6 小时（1h 读 + 4h 实现 + 1h 故障分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `agent_patterns.py`。
- **验收命令**：

```bash
python chapters/part4-agents-langgraph/4.1-agent-patterns/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

Agent 不是“让模型随便调工具”。一旦把控制权交给模型，就必须回答：

- 循环怎么停？
- 工具不在白名单怎么办？
- 参数错/超时/预算耗尽怎么退出？
- 失败会不会伪装成成功？
- 状态是覆盖还是追加？

这个 gate 用脚本化决策器代替模型，只验证控制循环本身。

## 任务

实现 `gate/starter.py` 的四个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `fixed_workflow` | 整数校验 + 加法；bool/非整数报错 |
| `scripted_planner` | 无观察 -> add；有观察 -> finish |
| `initial_state` | 完整初始 state |
| `build_graph` | LangGraph 有界循环：白名单、预算、失败出口 |

关键口径：

- 只允许 `add`；未知工具 -> `status=failed`，error 含“白名单”。
- `steps >= max_steps` -> `failed`，error 含“预算”。
- planner 抛 `ValueError/TimeoutError` -> `failed`；意外异常不吞。
- 工具参数错误 -> `failed`，不追加 observation。
- 正常路径 -> `status=done`，observations 含结果。
- `max_steps < 1` -> `ValueError`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | `fixed_workflow(2,3)` | 5 |
| 2 | bool/字符串参数 | `ValueError` |
| 3 | 正常 planner | done，observations=[5] |
| 4 | 一直 add，max_steps=2 | failed 预算，steps=2 |
| 5 | 未知工具 | failed 白名单 |
| 6 | planner 抛 ValueError | failed 记录原因 |
| 7 | add 参数是字符串 | failed，无 observation |
| 8 | max_steps=0 | `ValueError` |

## 验收标准

`gate_check.py` 的 8 项全部 PASS：

- 固定工作流、初始状态、正常循环、预算、白名单、planner 异常、参数错误、max_steps 校验。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么 Agent 循环必须有 `max_steps`？
2. 失败时为什么不能把 `status` 写成 done？
3. 哪些错误应该向外暴露，哪些应该转成 failed？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（8/8）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 4.1
```

对照时只回答：

1. 参考实现的 `decide` 节点检查了哪几层？
2. 参考实现的 `observations` 为什么返回新列表？
3. 检查点/暂停恢复在本 gate 里没有覆盖，为什么？

## 概念地图

- **工作流 vs Agent**：步骤写死 vs 模型决定下一步。
- **状态**：question/steps/observations/decision/status/error。
- **条件边**：按 status 决定去 tool 还是 END。
- **有界循环**：max_steps + 明确失败出口。
- **失败不伪装**：参数错误/预算耗尽都写 failed，不写 done。

## 边界

- gate 用脚本化 planner，不验证真实模型规划。
- 检查点/暂停恢复见参考实现与 4.10。
- 有副作用工具需要审批/幂等，见 4.8/4.11。
