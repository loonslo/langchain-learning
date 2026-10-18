# L4.4 ReAct 与工具设计 · Gate（原 4.5）

[全书目录](../../README.md) · [上一章 4.4](../4.4-state-reducer/README.md) · [下一章 4.6](../4.6-node-reliability/README.md)

- **能力**：设计工具 schema、校验参数、处理未知工具/异常、给有副作用的工具加审批，并把工具结果当不可信数据。
- **v2 路径**：L4.4 / 核心（Gate；ReAct 与工具设计）
- **前置**：4.3（分支与循环）、1.5（工具调用）。
- **时间盒**：8 小时（1h 读 + 5h 实现 + 2h 故障注入与记录）。
- **闭卷规则**：只读本页、`gate/starter.py`；**通过 gate 之前不要打开** `react_loop.py`、`react_reliability.py`、`react_agent.py`。
- **验收命令**：

```bash
python chapters/part4-agents-langgraph/4.5-react-agent/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 来绕过检查。

## 为什么做这个 gate

一个能跑通的 ReAct 循环只是起点。线上真正会出事的是：

- 模型选错工具、传错参数；
- 工具超时/抛异常；
- 模型陷入循环，一直调同一个工具；
- 有副作用的工具（删订单）被模型直接调用；
- 工具返回的内容里夹着“忽略之前的指令”，把 Agent 带偏。

这个 gate 不考“能不能调通一次工具”，而是考：

> 把模型当成不可靠的决策者，把工具当成有权限边界的副作用，把工具结果当成不可信数据。

## 任务

实现 `gate/starter.py` 的三个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `build_tools` | 三个工具：`lookup_order`、`refund_policy`、`delete_order`；元数据正确 |
| `validate_call` | 未知工具、非 dict、缺参数、参数类型错都返回可读错误 |
| `run_agent` | 解析 `Action:`/`Final:`；校验、审批、执行、包装、记录轨迹；有界终止 |

工具约定：

| 工具 | 参数 | 只读 | 审批 | 说明 |
|---|---|---|---|---|
| `lookup_order` | `{"order_id": str}` | 是 | 否 | 查订单状态 |
| `refund_policy` | `{"topic": str}` | 是 | 否 | 查退款政策 |
| `delete_order` | `{"order_id": str}` | 否 | **是** | 有副作用，必须人工审批 |

`run_agent` 的返回：

```python
{
    "answer": str,
    "trace": [
        {
            "step": 1,
            "tool": "lookup_order",
            "args": {"order_id": "A100"},
            "ok": True,
            "observation": "订单 A100：已发货",
            "error": None,          # 失败时是可读字符串
            "blocked": False,       # 审批未通过时 True
        }
    ],
    "stopped_reason": "final" | "max_steps" | "unparsed" | "model_error",
}
```

关键约束：

- 未知工具/非法 JSON/参数错误/工具异常都不能让程序崩；轨迹里要有 `ok=False` 和 `error`。
- `delete_order` 没有 `approve` 或 `approve` 返回 `False` 时不得执行；轨迹标记 `blocked=True`。
- 工具结果回灌模型前必须包在 `<untrusted_tool_result>...</untrusted_tool_result>` 里；结果里自带的结束标签必须被转义，不能让它提前关闭。
- 达到 `max_steps` 必须停止；`max_steps < 1` 抛 `ValueError`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | `Action: lookup_order[not-json]` | `ok=False`、`error=invalid_args`，不崩 |
| 2 | 模型请求未知工具 | `error=unknown_tool`，仍可收尾 |
| 3 | 缺 `order_id` | `error=invalid_args` |
| 4 | 未审批就调 `delete_order` | `blocked=True`、`error=approval_required`，handler 不执行 |
| 5 | `approve` 回调抛异常 | `blocked=True`、`error=approval_error` |
| 6 | 工具 handler 抛异常 | `error=tool_error`，不崩 |
| 7 | 模型一直调工具 | `max_steps` 停止，轨迹步数等于上限 |
| 8 | 工具结果含 `</untrusted_tool_result>` | 包装后只出现一次结束标签 |
| 9 | 模型输出既不是 Action 也不是 Final | 保留原文，`unparsed` |
| 10 | 模型调用抛异常 | `model_error`，不崩 |

## 验收标准

`gate_check.py` 的 14 项全部 PASS：

- 工具表：三个工具、只读/审批元数据、handler 可用。
- 校验：合法、未知工具、缺参数、非 dict、类型错。
- 正常路径：调用工具后 `Final`，轨迹结构正确，结果被包装。
- 故障：非法 JSON、未知工具、未审批删除、审批异常、工具异常、超步数、无法解析、模型异常。
- 安全：工具结果不能自行关闭不可信标记。

通过后，在 [workbook.md](workbook.md) 写：

1. 哪一类失败最容易被“模型看起来答对了”掩盖？
2. 为什么审批要放在执行之前，而不是执行后记录？
3. 如果工具结果是网页内容，除了包装，还需要哪些防护？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（14/14）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 4.5 react_loop.py
python tools/run_chapter.py 4.5 react_reliability.py
```

对照时只回答：

1. 参考实现用 LangGraph 的 `tools_condition` 控制循环；你的 `run_agent` 用什么条件？
2. 参考实现有没有把工具结果标记为不可信？如果没有，风险是什么？
3. 参考实现的工具都是无副作用的；把 `delete_order` 加进去，需要改哪几层？

## 概念地图

- **工具 schema**：参数名、类型、是否必需；模型输出不可信，必须先校验再执行。
- **审批边界**：有副作用的工具在执行前需要人工/策略确认；事后记录不能阻止副作用。
- **不可信数据**：工具结果可能包含指令；包装 + 转义 + prompt 约束，三层一起用。
- **有界循环**：`max_steps` + 明确出口；没有上限的 Agent 是成本与延迟事故。
- **可读失败**：未知工具、参数错、超时、审批失败都要给用户/日志可读原因。

## 边界

- 本章用脚本化模型输出，不调用真实模型；通过 gate 只证明控制流和边界正确。
- 审批回调是示例；真实系统要接身份、权限、审计和一次性令牌（4.11、10.1）。
- 工具结果包装不能替代输出过滤、权限检查和内容安全（5.7）。
