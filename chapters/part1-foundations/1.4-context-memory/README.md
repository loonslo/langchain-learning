# 1.4 多轮上下文：记住谁说过什么

[全书目录](../../README.md) · [上一章 1.3](../1.3-structured-output/README.md) · [下一章 1.5](../1.5-tool-calling/README.md)

- **目标**：让多轮对话记住上文，并用 `session_id` 隔离不同会话。
- **前置**：1.1。
- **环境**：调用真实模型。
- **命令**：`python tools/run_chapter.py 1.4`

## 问题

第二句问“我刚才说我在学什么？”，模型答不出来：每次 `invoke` 都是独立的请求，它不知道上一句。要让对话连贯，必须由程序把历史再发给模型。

## 概念

- **模型无状态**：所谓记忆，是每次请求都把历史消息重新放进 prompt。历史越长，成本和上下文占用越大。
- **`MessagesPlaceholder`**：prompt 中预留的“历史对话”插槽，变量名为 `history`。
- **`RunnableWithMessageHistory`**：自动读取历史填进插槽，调用结束后再把这一轮写回历史。
- **`session_id`**：会话标识。同一个 id 共用一段历史，换 id 就是互不相干的新会话；不隔离用户和会话，记忆就会串台。
- **`InMemoryChatMessageHistory`**：历史存在内存里，程序退出即丢失。

## 流程

1. 在 prompt 中加入 `MessagesPlaceholder("history")` 与本轮的 `{question}`。
2. 用字典 `store` 按 `session_id` 保存各会话的历史，`get_session_history` 负责取出或新建。
3. 用 `RunnableWithMessageHistory` 包住基础链，指明输入变量 `question` 与历史变量 `history`。
4. 同一个 `session_id` 连问三轮，观察第三轮能否答出第一轮说过的名字。

## 代码导读

[context_memory.py](context_memory.py)：先看 prompt 里的插槽，再看 `store` 和 `get_session_history`，最后看 `RunnableWithMessageHistory` 的两个 key 参数与 `config`。

## 练习

1. 用两个不同的 `session_id` 各聊几句，验证两段记忆互不影响。
2. 三轮对话之后换成新的 `session_id`，再问“我叫什么名字？”，观察模型如何回答。
3. 估算聊到第 20 轮时每次请求要带多少历史，思考何时需要截断或摘要（4.10 讨论上下文管理）。

## 运行与边界

- 会调用真实模型并产生少量费用。
- 内存历史不持久，也没有长度上限；生产环境用 LangGraph 的 checkpoint（4.10）等方案。
- `RunnableWithMessageHistory` 在新版会提示弃用警告，脚本已忽略；它在这里只用来讲清历史怎样进入 prompt。
