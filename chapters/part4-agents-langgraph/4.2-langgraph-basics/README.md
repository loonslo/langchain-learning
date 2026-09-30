# 4.2 LangGraph 基础：一份状态经过两个节点

[全书目录](../../README.md) · [上一章 4.1](../4.1-agent-patterns/README.md) · [下一章 4.3](../4.3-branch-loop/README.md)

- **目标**：认清 LangGraph 的三个基本件（State、Node、Edge），搭出最小的线性图。
- **前置**：1.1（LCEL 管道）、4.1。
- **环境**：离线，不调用模型。
- **命令**：`python tools/run_chapter.py 4.2 graph_basics.py`

## 问题

LCEL 的 `|` 是一条直线走到底。真实 Agent 还需要循环（没答好再来一轮）、分支（按情况走不同的路）和状态（中途保存中间结果），这些 LCEL 做不到，要用图。LangGraph 就是用图描述带状态的流程。

## 概念

- **State**：贯穿全程的一份数据，用 `TypedDict` 声明有哪些字段。
- **Node**：一个函数，读 state，返回“要更新的字段”（部分 dict），LangGraph 自动合并回 state。
- **Edge**：连接节点、决定顺序；`START` 是入口，`END` 是出口。
- **线性图与 LCEL 没有本质差别**：图的价值在分支、循环和状态，那是 4.3 的内容。合并规则（reducer）默认是覆盖，4.4 详细讲。

## 流程

`graph_basics.py`：

1. 声明 `DraftState`（`topic`、`draft`、`polished`）。
2. `write_draft` 写初稿，`polish` 润色；每个节点只返回自己负责的字段。
3. `START → write_draft → polish → END`，`compile()` 得到可运行的图。
4. `invoke({"topic": ...})` 传入初始 state，运行结束返回完整的最终 state。

## 代码导读

| 文件 | 内容 |
|---|---|
| [graph_basics.py](graph_basics.py) | 主线：写稿 → 润色的最小线性图，先读它 |
| [linear_graph.py](linear_graph.py) | 同一骨架的通用模板：只用 `history` 记录流程轨迹，去掉业务语义 |
| [conditional_graph.py](conditional_graph.py) | 预告 4.3：在线性主干上加条件分支和循环（`step_c` 校验不通过就回到 `step_b`），靠 `attempts` 防止死循环 |

## 练习

1. 给 `graph_basics.py` 的图再加一个 `review` 节点（`polish → review → END`），在 state 里加 `review` 字段，观察最终 state 多了什么。
2. 对每张图回答“建体感三问”：有哪些字段？每步改了什么？走的什么顺序？
3. 阅读 `conditional_graph.py` 的输出，说明循环是怎样由“条件边指回上游节点”形成的。

## 运行与边界

- 三个脚本都不调用模型，只演示控制流。
- `conditional_graph.py` 在节点里手动拼接 `history`，只是为了不引入 reducer；更稳妥的做法见 4.4。
