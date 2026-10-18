# L4.5 结构化路由 · Gate（原 4.7）

[全书目录](../../README.md) · [上一章 4.6](../4.6-node-reliability/README.md) · [下一章 4.8](../4.8-plan-and-execute/README.md)

- **能力**：把模型路由输出限制在枚举集合内；解析失败/非法值有明确出口。
- **v2 路径**：L4.5 / 核心（Gate；结构化路由）
- **前置**：4.6（节点可靠性）、1.3（结构化输出）。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 故障分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `structured_routing.py`。
- **验收命令**：

```bash
python chapters/part4-agents-langgraph/4.7-structured-routing/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

用关键词匹配猜模型意图，是生产路由最常见的脆弱点：

- 模型说“先 RESEARCH 再 WRITING”，两个关键词同时命中；
- 输出缺字段/多解释，解析崩；
- 值不在允许集合里，路由到不存在的节点；
- 分类标签拼错，分支永远走不到。

这个 gate 用固定 JSON 文本，验证解析、枚举校验、路由函数和意图分类。

## 任务

实现 `gate/starter.py` 的三个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `parse_route` | 解析 `{"next":...}`；缺字段/非法 JSON/值不在 allowed -> `ValueError` |
| `route_next` | done -> `"end"`；否则返回 `_next`；非法 -> `ValueError` |
| `parse_intent` | 解析 `{"category":...}`；只允许三类 |

关键口径：

- 允许集合由调用方传入，不在集合内就失败。
- 解析失败不返回默认值，避免“静默走错分支”。
- `route_next` 的 `_next` 只允许 `research/writing/review`。
- 意图只允许 `knowledge/data_query/chitchat`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 合法 route JSON | 返回 next |
| 2 | 非 JSON / 数组 / 缺 next | `ValueError` |
| 3 | next 不在 allowed | `ValueError` |
| 4 | done=True | `"end"` |
| 5 | `_next` 非法 | `ValueError` |
| 6 | 意图三类 / 未知类别 | 正常 / `ValueError` |

## 验收标准

`gate_check.py` 的 4 项全部 PASS：

- 枚举路由解析、拒绝非法路由、路由函数、意图解析。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么路由失败不能默认走某条分支？
2. 枚举校验和关键词匹配的差别是什么？
3. 解析失败时，程序应该重试、降级还是转人工？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（4/4）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 4.7
```

对照时只回答：

1. 参考实现用 `PydanticOutputParser`，你的 gate 用 JSON；两者约束力差在哪？
2. 参考实现的 `route` 为什么能“零歧义”？
3. 参考实现没有解析失败兜底；上生产要先补什么？

## 概念地图

- **结构化路由**：模型输出枚举/JSON，代码读确定字段。
- **枚举**：把选择限制在可验证集合内。
- **解析失败**：不能默认走某条路，要明确失败/降级。
- **意图分类**：knowledge/data_query/chitchat 分流。
- **代价**：多一次约束，换可测/可复现。

## 边界

- gate 用固定文本，不调用真实模型。
- 通过 gate 只证明解析/校验结构正确，不证明模型分类准确。
- 真实 PydanticOutputParser、Supervisor 图见参考实现。
