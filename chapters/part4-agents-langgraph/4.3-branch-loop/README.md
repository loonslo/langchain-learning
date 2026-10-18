# L4.3 分支与循环 · Gate（原 4.3）

[全书目录](../../README.md) · [上一章 4.2](../4.2-langgraph-basics/README.md) · [下一章 4.4](../4.4-state-reducer/README.md)

- **能力**：用条件边实现分支/循环；用达标条件终止；用 `recursion_limit` 兜底。
- **v2 路径**：L4.3 / 核心（Gate；分支与循环）
- **前置**：4.2（线性图）、1.5（工具循环）。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `branch_loop.py`。
- **验收命令**：

```bash
python chapters/part4-agents-langgraph/4.3-branch-loop/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

循环是图的核心，也是最容易写出死循环的地方：

- 条件边路由错，永远到不了 END；
- 达标线写错，多跑或少跑；
- 没有 `recursion_limit`，配置错误时无限循环；
- 节点返回整个 state 而不是部分字段，覆盖掉别的字段；
- 计数器不递增，退出条件永远不满足。

这个 gate 用质量分自循环，验证节点、路由、循环和步数安全阀。

## 任务

实现 `gate/starter.py` 的三个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `improve` | quality/rounds 各 +1，返回部分 dict |
| `route` | quality>=5 -> `good_enough`，否则 `keep_going` |
| `build_loop` | START→improve；条件边指回 improve 或 END |

关键口径：

- `improve` 不修改输入 state。
- `route` 只读 state，返回字符串。
- `build_loop().invoke({"quality":0,"rounds":0})` -> `{"quality":5,"rounds":5}`。
- `recursion_limit=4` 时必须抛 `GraphRecursionError`，不能静默死循环。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | improve(1,2) | (2,3) |
| 2 | route(4) / route(5) | keep_going / good_enough |
| 3 | 从 0 分跑 | 5 轮到达标 |
| 4 | recursion_limit=4 | GraphRecursionError |

## 验收标准

`gate_check.py` 的 4 项全部 PASS：

- improve 节点、route 分支、循环到达标、recursion_limit 防护。

通过后，在 [workbook.md](workbook.md) 写：

1. 条件边指回上游，为什么必须配退出条件？
2. `recursion_limit` 和业务达标条件各防什么？
3. 节点返回整个 state 会有什么问题？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（4/4）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 4.3 branch_loop_examples.py
python tools/run_chapter.py 4.3 branch_loop.py
```

对照时只回答：

1. 参考实现的 `route` 和你的返回值一致吗？
2. 参考实现的 `recursion_limit` 例子为什么从 0 分跑到 5 分只需要 4 步？
3. 参考实现后半段用 `tools_condition`/`ToolNode`，它们替手写循环做了什么？

## 概念地图

- **条件边**：路由函数返回语义名，映射到节点/END。
- **循环**：条件边指回上游；必须有退出条件。
- **达标条件**：业务退出（quality>=5）。
- **安全阀**：recursion_limit 防配置错误/意外循环。
- **harness**：工具解析、执行、记忆、中断恢复。

## 边界

- gate 只跑离线质量分循环，不调用模型。
- 通过 gate 只证明控制流正确，不证明 Agent 任务完成。
- 工具循环/记忆见参考实现后半段与 4.5/4.10。
