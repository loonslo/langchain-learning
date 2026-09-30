# 4.9 可观测性：把运行过程留成证据

[全书目录](../../README.md) · [上一章 4.8](../4.8-plan-and-execute/README.md) · [下一章 4.10](../4.10-checkpoint-context/README.md)

- **目标**：让 Agent 的每一步都看得见、可复盘：会用 `stream_mode`，并把每步轨迹落盘成 JSONL。
- **前置**：4.8。
- **环境**：离线，不调用模型；【三】的 LangSmith 追踪可选。
- **命令**：`python tools/run_chapter.py 4.9`

## 问题

Agent 最难的不是搭出来，而是它答错时你不知道错在哪一步。生产 Agent 必须每一步可观察、可复盘。

## 概念

三层可观测，从内到外：

1. **`stream_mode` 四件套**：`updates`（每个节点这一步改了哪些字段，调试首选）、`values`（每步之后的完整 state）、`messages`（逐 token 流式输出，做打字机效果）、`debug`（最详细，含节点进出和类型）。
2. **结构化轨迹落盘**：把每一步（节点名、相对耗时、更新的字段、内容摘要）写成 JSONL，一行一步。出错时可以 grep、按耗时找最慢的步骤、与上次的轨迹 diff。比 `print` 强在可检索、可回归。
3. **LangSmith 追踪**：在 `.env` 里设置 `LANGSMITH_TRACING=true` 和 `LANGSMITH_API_KEY`，之后每次运行自动上报，网页里看完整调用树（3.6 已经用过）。

## 流程

`observability.py`：

1. 【一】对一个“计划 → 写作 → 审核”的小图，分别用 `updates`、`values`、`debug` 三种模式流式输出，比较看到的信息有什么不同。
2. 【二】`run_with_trace` 在运行图的同时，把每步写入本章目录下的 `reports/agent_trace.jsonl`，再逐行读回并打印节点名、耗时和更新的字段。
3. 【三】不需要额外代码：配置了上面的环境变量后，这些运行会自动出现在 LangSmith 里。

## 代码导读

[observability.py](observability.py)：先看 `build` 里的小图，再看 `demo_stream_modes` 里三种模式的输出，最后看 `run_with_trace` 每条记录里有哪些字段。

## 练习

1. 对比三种 `stream_mode` 的输出，说明调试时该选哪一种。
2. 打开生成的 `agent_trace.jsonl`，找出最慢的一步。
3. 给 4.12 的搜索 Agent 用 `stream_mode="messages"` 做打字机式输出，同时把每步轨迹落盘到 `reports/`。

## 运行与边界

- 轨迹里只存内容摘要；含隐私的输入不要原样落盘。
- 本章只覆盖离线的图，真实模型的耗时和失败还需要在真实运行中采集。
