# L4.2 LangGraph 基础 · Gate（原 4.2）

[全书目录](../../README.md) · [上一章 4.1](../4.1-agent-patterns/README.md) · [下一章 4.3](../4.3-branch-loop/README.md)

- **能力**：用 State/Node/Edge 搭线性图；用条件边把流程接成有出口的循环。
- **v2 路径**：L4.2 / 核心（Gate；LangGraph 基础）
- **前置**：4.1（Agent 模式）、1.1（LCEL）。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `linear_graph.py` / `conditional_graph.py`。
- **验收命令**：

```bash
python chapters/part4-agents-langgraph/4.2-langgraph-basics/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

线性图只是“用图写管道”。真正的价值在分支/循环，而循环必须有出口：

- 状态字段缺失，节点一读就崩；
- 条件边路由错，循环不终止；
- 图之间共享可变状态，结果互相污染；
- 从中间状态恢复时，计数不对。

这个 gate 用最小图验证状态传递、分支循环和状态隔离。

## 任务

实现 `gate/starter.py` 的两个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `build_linear` | START → step_a → step_b → END；history 两条 |
| `build_conditional` | START → step_a → step_b → step_c；不通过回 step_b；attempts>=2 通过 |

关键口径：

- 线性图的 state 只需要 `history`。
- 条件图 state：`history/attempts/approved`；step_b 让 attempts+1。
- step_c 在 attempts>=2 时 approved=True，路由到 END；否则回 step_b。
- 从 attempts=1 开始，应再走一轮后通过。
- 图之间不共享状态。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 线性图初始 history=[] | 两条记录、顺序正确 |
| 2 | 条件图 attempts=0 | attempts=2、approved=True |
| 3 | 条件图 attempts=1 | 再走一轮、attempts=2 |
| 4 | 两次 invoke | 结果互不影响 |

## 验收标准

`gate_check.py` 的 4 项全部 PASS：

- 线性顺序、分支循环/审批、从中间状态继续、图之间状态隔离。

通过后，在 [workbook.md](workbook.md) 写：

1. 线性图和 LCEL 的本质差别是什么？
2. 条件边指回上游，为什么必须配计数器/退出条件？
3. 状态字段缺失时，节点应该报错还是给默认值？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（4/4）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 4.2 graph_basics.py
python tools/run_chapter.py 4.2 linear_graph.py
python tools/run_chapter.py 4.2 conditional_graph.py
```

对照时只回答：

1. 参考实现的 `graph_basics.py` 和你的 `build_linear` 结构是否一致？
2. 参考实现的 `conditional_graph.py` 用什么防死循环？
3. 参考实现用 `history` 手动拼接，和 reducer 有什么区别？

## 概念地图

- **State**：TypedDict 声明字段；跨节点传递。
- **Node**：读 state，返回部分 dict。
- **Edge**：START/END 与普通边；顺序写死。
- **条件边**：按 state 路由；指回上游形成循环。
- **出口**：计数器/阈值/失败状态，循环必须有终止条件。

## 边界

- gate 不调用模型，只验证控制流。
- 通过 gate 只证明状态/边结构正确，不证明业务逻辑正确。
- reducer 合并规则见 4.4；检查点见 4.10。
