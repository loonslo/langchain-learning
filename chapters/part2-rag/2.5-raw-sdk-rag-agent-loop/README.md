# 2.5 裸 SDK 与循环：看清框架封装了什么

[全书目录](../../README.md) · [上一章 2.4](../2.4-eval-seed/README.md) · [下一章 2.6](../2.6-pdf-sources/README.md)

- **目标**：不用 LangChain，只用标准库和 HTTP 接口手写检索、问答和最小的 Agent 循环，看清框架封装了什么。
- **前置**：2.3。
- **环境**：没有 `DEEPSEEK_API_KEY` 时，`chat()` 返回固定的离线提示，流程仍可读可跑；配置密钥后调用真实模型。
- **命令**：`python tools/run_chapter.py 2.5`

## 问题

框架几行就能搭出 RAG，但出错时不知道该看哪一层。手写一遍，才能看清模型之外的工程代码（harness）：检索、prompt 拼接、工具解析、循环控制、停止条件和错误兜底。

## 概念

- **Harness**：模型之外的工程层。框架封装的不是魔法，正是这些代码。
- **TF 余弦检索**：用词频向量的余弦相似度近似检索，不需要 embedding 模型。效果不如向量检索，只用来演示检索逻辑；分数为 0 的片段不返回。
- **ReAct 风格循环**：模型输出 `Action: 工具名[参数]` 表示要调用工具，输出 `Final: 答案` 表示结束；程序解析动作、执行工具，把 `Observation: 结果` 追加回对话，再让模型继续。
- **停止条件**：`max_steps` 防止无限调用工具；解析不到动作时，把模型输出当作最终回答。

## 流程

RAG 部分：`split_text` 切块 → `retrieve` 按 TF 余弦取 top-k → 没有命中直接返回“文档中没有提到” → 有命中则拼上下文并调用 `chat`。

Agent 部分：`agent_loop` 最多 4 步，每步：调用模型 → 是 `Final:` 则返回 → 否则 `parse_action` → 执行 `TOOLS` 里的工具 → 把 Observation 追加回对话。

## 代码导读

[raw_sdk_rag_agent_loop.py](raw_sdk_rag_agent_loop.py)：先读 `tokenize`、`score`、`retrieve`（检索），再读 `chat`（直接调用接口），最后读 `parse_action` 与 `agent_loop`。

## 练习

1. 不配置密钥运行一次，读懂离线提示；配置后再对比真实回答。
2. 把 `max_steps` 改成 1，观察停止条件的表现。
3. 让模型请求一个不存在的工具，观察“未知工具”的兜底，思考为什么必须有它。

## 运行与边界

- `calculator` 用受限的 `eval` 只是演示，不能执行不可信输入（5.7）。
- 关键词式检索对同义表达不敏感，不能替代 embedding。
- 有密钥时会调用真实模型并产生费用。
