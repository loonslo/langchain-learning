# L1.5 工具调用 · Gate（原 1.5）

[全书目录](../../README.md) · [上一章 1.4](../1.4-context-memory/README.md) · [下一章 1.6](../1.6-mcp-intro/README.md)

- **能力**：定义工具 schema；校验参数；执行工具并把结果回灌；未知工具/异常/超步数都有出口。
- **v2 路径**：L1.5 / 核心（Gate；工具调用）
- **前置**：1.1（一次调用）。
- **时间盒**：6 小时（1h 读 + 4h 实现 + 1h 故障分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `tool_calling.py`。
- **验收命令**：

```bash
python chapters/part1-foundations/1.5-tool-calling/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

工具调用是 Agent 的地基，也是最容易出事故的地方：

- 模型请求不存在的工具；
- 参数缺字段/类型错；
- 工具函数自己抛异常；
- 工具返回非字符串，拼接时崩；
- 模型一直请求工具，循环停不下来；
- 结果没有以 `tool` 消息回灌，模型看不到事实。

这个 gate 让你把“模型只负责请求，程序负责执行”做成可验证的循环，而不是把 `tool_calls` 直接 `eval`。

## 任务

实现 `gate/starter.py` 的三个部分：

| 部分 | 你要交付的行为 |
|---|---|
| `build_tools` | `get_weather`、`calculate` 两个工具，schema/description/handler 正确 |
| `dispatch_tool` | 未知工具、非 dict、缺参数、类型错、工具异常、非字符串结果都有可读错误 |
| `run_tool_loop` | 模型请求 → 执行 → 结果回灌 → 再请求；有界终止；异常降级 |

关键口径：

- `ToolSpec.parameters` 是 `{"参数名": 类型}`；只校验必需字段和类型。
- `dispatch_tool` 返回 `{"ok","result","error"}`；成功时 `error=None`。
- `run_tool_loop` 的 `llm_fn(messages)` 返回 `{"content","tool_calls"}`；`tool_calls` 元素含 `id/name/args`。
- 工具结果必须以 `{"role":"tool","content":...,"tool_call_id":...}` 追加回 `messages`。
- `max_steps < 1` 抛 `ValueError`；`llm_fn` 异常 -> `stopped_reason="model_error"`。
- 未知工具/参数错误/工具异常不崩，记录 `trace`，继续循环。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 请求 `nope` 工具 | `error="unknown_tool"` |
| 2 | `args` 不是 dict | `error="invalid_args"` |
| 3 | 缺 `city` / `city` 是 int | `error="invalid_args"` |
| 4 | 工具 handler 抛异常 | `error="tool_error"` |
| 5 | 工具返回非 str | `error="invalid_tool_output"` |
| 6 | 模型一直请求工具 | `stopped_reason="max_steps"` |
| 7 | 模型调用抛异常 | `stopped_reason="model_error"` |
| 8 | 工具结果回灌 | 第二次调用能看到 `role="tool"` 和 `tool_call_id` |

## 验收标准

`gate_check.py` 的 11 项全部 PASS：

- 工具表/元数据、合法分发、3 类参数错误、工具异常。
- 无工具直接回答、工具回灌后收尾、未知工具、工具异常、超步数、模型异常、`max_steps=0`。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么 `tool_calls` 不能直接 `eval` 执行？
2. 工具结果回灌时，`tool_call_id` 起什么作用？丢了会怎样？
3. 如果工具有副作用（退款/删除），这个循环还缺哪几层？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（11/11）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 1.5
```

对照时只回答：

1. 参考实现用 `@tool` + `bind_tools`，谁负责生成工具 schema？你的 gate 里是谁？
2. 参考实现只跑两轮；如果模型连续请求工具，它有没有上限？
3. 参考实现的 `calculate` 用 `eval`；你的 `dispatch_tool` 有没有类似风险？

## 概念地图

- **工具 schema**：名字、说明、参数类型；模型靠它选工具。
- **模型只请求**：执行权在程序；参数必须校验后才能进 handler。
- **结果回灌**：`role="tool"` + `tool_call_id`，模型才能把结果对上是哪次请求。
- **有界循环**：`max_steps` + 明确出口；没有上限的循环会烧钱、拖延迟。
- **可读失败**：未知工具/参数错/异常都要能解释，不能只打印堆栈。

## 边界

- gate 用脚本化模型，不调用真实模型；真实 function calling 的稳定性另验。
- 通过 gate 只证明工具循环结构正确，不证明模型选工具准确。
- 审批、权限、审计、幂等见 L4.8/L5.4。
