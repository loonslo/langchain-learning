# L1.3 结构化输出 · Gate（原 1.3）

[全书目录](../../README.md) · [上一章 1.2](../1.2-control-output/README.md) · [下一章 1.4](../1.4-context-memory/README.md)

- **能力**：把模型输出解析成带字段的数据；校验类型与业务范围；失败时只修复一次。
- **v2 路径**：L1.3 / 核心（Gate；结构化输出）
- **前置**：1.1（一次调用）。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 故障分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `structured_output.py`。
- **验收命令**：

```bash
python chapters/part1-foundations/1.3-structured-output/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

“让模型输出 JSON”在 demo 里很顺，在生产里会遇到：

- 模型在 JSON 外面加解释文字，或者用 Markdown 围栏；
- 字段少一个、类型不对（分数变成字符串、`true` 当整数）；
- 分数越界、问题列表里混入非字符串；
- 解析失败后无限重试，成本失控。

这个 gate 让你把结构化输出做成 **解析 → 校验 → 一次修复 → 明确失败**，而不是 `json.loads` 一把梭。

## 任务

实现 `gate/starter.py` 的两个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `parse_model_json` | 解析纯 JSON/围栏/带说明文字；按 schema 校验字段与类型；失败只修复一次 |
| `validate_code_review` | 校验 `summary/issues/score`，返回规范化结果；非法抛 `SchemaError` |

关键口径：

- `schema` 是 `{"字段": 类型}`，例如 `{"summary": str, "issues": list, "score": int}`。
- `int` 不接受 `bool`；`list` 只校验容器，元素类型由业务函数再校验。
- 解析/校验失败时，`repair_fn` 最多调用 **一次**；没有 `repair_fn` 直接失败。
- `validate_code_review`：summary 去空白后非空；issues 全是字符串；score 是 1–10 的整数。
- 任何不合法抛 `SchemaError`，不要把底层异常直接抛给调用方。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 纯 JSON | 正常解析 |
| 2 | ```json 围栏 + 前后说明文字 | 正常解析 |
| 3 | 缺 `score` | `SchemaError` |
| 4 | `score: "8"` / `true` / `issues: "x"` | `SchemaError` |
| 5 | JSON 是数组/字符串/数字 | `SchemaError` |
| 6 | 非法 JSON + repair 返回合法 JSON | 成功，repair 只调一次 |
| 7 | 非法 JSON + repair 仍非法 | `SchemaError` |
| 8 | 非法 JSON + 无 repair | `SchemaError` |
| 9 | score 0 / 11 / True | `SchemaError` |
| 10 | issues 含非字符串 | `SchemaError` |

## 验收标准

`gate_check.py` 的 10 项全部 PASS：

- 解析：纯 JSON、围栏、说明文字、缺字段、类型错、非对象。
- 修复：成功一次、失败、无 repair。
- 业务校验：合法审查结果、6 类非法结果。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么修复只能做一次？无限修复的代价是什么？
2. 类型校验通过后，为什么还要校验 `score` 的业务范围？
3. 如果模型持续输出非法结构，服务应该返回什么、记录什么？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（10/10）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 1.3
```

对照时只回答：

1. 参考实现用 `with_structured_output`，它把“格式约束”交给了谁？你的解析器补了什么？
2. 参考实现拿到的是 Pydantic 对象；你的 gate 返回 dict。两者在后续评测里各有什么取舍？
3. 参考实现没有业务范围校验；把 score 改成 0–100 后，哪里需要改？

## 概念地图

- **结构化输出**：字段名 + 类型 + 说明，让程序能直接使用。
- **格式 vs 语义**：类型正确不代表内容正确；业务校验要单独做。
- **一次修复**：给模型/解析器一次纠错机会；再失败就明确报错，避免成本和延迟失控。
- **SchemaError**：把解析/校验失败变成可读错误，方便上层重试或降级。
- **Pydantic 对象 vs dict**：对象有类型提示；dict 更轻、更容易跨层传递。

## 边界

- gate 用假文本，不调用真实模型；真实 function calling 的稳定性另验。
- 通过 gate 只证明解析/校验/修复结构正确，不证明字段内容正确。
- 业务规则（如严重级别枚举、复现步骤必填）要按场景继续加。
