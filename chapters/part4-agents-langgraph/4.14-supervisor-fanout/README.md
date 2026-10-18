# L4.9 Supervisor 与并行 · Gate（原 4.14）

[全书目录](../../README.md) · [上一章 4.13](../4.13-text2sql-agent/README.md) · [下一章 4.15](../4.15-framework-landscape/README.md)

- **能力**：用固定流水线推进 Supervisor；对 fan-out 分支结果做去重保序的 fan-in。
- **v2 路径**：L4.10 / 核心（Gate；Supervisor/Fan-out（可跳））
- **前置**：4.4（reducer）、4.5、4.8。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `langgraph_supervisor.py`。
- **验收命令**：

```bash
python chapters/part4-agents-langgraph/4.14-supervisor-fanout/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

多 Agent 最容易出这些错：

- Supervisor 阶段推进错，research 后直接 FINISH；
- 未知阶段不报错，路由到不存在的节点；
- 流水线为空，取下标崩；
- fan-out 结果直接拼接，重复/顺序乱；
- 没有去重，汇总内容重复。

这个 gate 把“阶段推进”和“结果合并”抽成纯函数，验证边界和保序。

## 任务

实现 `gate/starter.py` 的两个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `next_stage` | 空 -> 第一阶段；最后 -> FINISH；未知/非法 pipeline -> `ValueError` |
| `fan_in` | 按输入顺序展平、去重保序；非 list -> `ValueError` |

关键口径：

- 默认流水线 `research → writing → review → FINISH`。
- 自定义 pipeline 也要支持；空/非 list -> `ValueError`。
- 未知 stage -> `ValueError`。
- fan-in 保持首次出现顺序，重复项只保留一次。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 空/research/writing/review | research/writing/review/FINISH |
| 2 | 自定义 [a,b] | a→b→FINISH |
| 3 | 未知阶段 | `ValueError` |
| 4 | 空 pipeline / 字符串 pipeline | `ValueError` |
| 5 | [["a","b"],["b","c"],["a"]] | ["a","b","c"] |
| 6 | 空输入 / 非 list | [] / `ValueError` |

## 验收标准

`gate_check.py` 的 5 项全部 PASS：

- 固定流水线、自定义流水线、未知阶段、非法 pipeline、fan-in 合并。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么 Supervisor 更适合固定流水线而不是让模型自由路由？
2. fan-in 为什么要去重保序？
3. 多 Agent 的协调成本体现在哪里？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（5/5）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 4.14
```

对照时只回答：

1. 参考实现的 `supervisor_node` 和你的 `next_stage` 是否一致？
2. 参考实现的 fan-out 用了什么 reducer？
3. agent-as-tool 和图上节点，上下文隔离差别在哪？

## 概念地图

- **Supervisor**：协调者按进度派活；固定流水线最可控。
- **Fan-out/Fan-in**：并行分支 + 汇聚；写同字段要 reducer。
- **去重保序**：合并结果可复现。
- **agent-as-tool**：子 Agent 独立上下文，只回摘要。
- **成本**：多 Agent 增加调用、延迟、调试成本。

## 边界

- gate 只测纯函数，不跑 LangGraph 多 Agent/真实模型。
- 通过 gate 只证明阶段推进/合并结构正确。
- 真实并行时序、reducer、委派见参考实现与 4.4。
