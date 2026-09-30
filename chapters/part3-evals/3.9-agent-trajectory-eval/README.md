# 3.9 Agent 轨迹评测：结果正确还不够

[全书目录](../../README.md) · [上一章 3.8](../3.8-prompt-ab-judge/README.md) · [下一章 3.10](../3.10-eval-report-failures/README.md)

- **目标**：理解 Agent 评测为什么不能只看最终答案，学会按工具调用轨迹判定行为是否合规。
- **前置**：3.2–3.5（RAG 评测）。
- **环境**：离线；评测的是合成轨迹，不需要先会写 Agent，也不调用模型。
- **命令**：`python tools/run_chapter.py 3.9`

## 问题

Agent 的回答很体面，行为却可能违规：比如答案说“已请求审批”，过程中却偷偷调用了 `delete_database`。只看最终答案的 RAG 式评测判它通过，看轨迹才发现违规。回答体面不等于行为安全。

## 概念

- **RAG 评测看答案**：关键词、引用、拒答；只看回答了什么，不看怎么回答的。
- **Agent 评测看轨迹**：该调的工具调了没有（`expected_ok`）、不该调的调了没有（`forbidden_ok`）、任务是否完成（`completed`）、有没有绕远路（`step_count` 与 `max_steps`）、是否真的用了工具（`min_tool_calls`）。
- **评测集字段**：与 RAG 共享 `id`、`question`、`should_refuse`、`keywords`；独有 `expected_tools`、`forbidden_tools`、`max_steps`、`min_tool_calls`。
- **合成轨迹**：本章的轨迹是手写的，用来讲清规则；真实系统需要采集真实的事件轨迹。

## 流程

1. 读 12 条 Agent 场景（工具选择、多步协作、安全屏障三类）。
2. 对每条场景，用合成轨迹调用 `evaluate_trajectory`，得到各项判定与通过与否。
3. 汇总：整体通过率、期望工具正确率、禁用工具规避率、任务完成率、未超步数比率等。
4. `demonstrate_rag_vs_agent` 对照同一场景：RAG 式评测判通过，Agent 式评测判违规。

## 代码导读

[trajectory_eval.py](trajectory_eval.py)：先看开头对两种评测差异的说明和评测集字段表，再看 `evaluate_trajectory` 里的各项判定，最后看 `demonstrate_rag_vs_agent`。

## 练习

1. 找到 `agent_041`，对比 RAG 式与 Agent 式评测的结论，解释为什么会相反。
2. 给某个场景新增一个禁用工具，改一条合成轨迹让它违规，确认判定为失败。
3. 想一想：真实 Agent 的轨迹应从哪里采集（日志、trace）？哪些字段必须记录？（4.9 讨论可观测性。）

## 运行与边界

- 合成轨迹只能证明评测规则本身正确，不代表真实 Agent 的表现。
- 关键工具调用的顺序、参数和副作用还需要更细的检查，8.6 继续展开。
