# 1.1 首次模型调用：让一条请求往返

[全书目录](../../README.md) · [上一章 0.2](../../part0-setup/0.2-learning-workflow/README.md) · [下一章 1.2](../1.2-control-output/README.md)

- **目标**：调用一次模型并读懂返回对象，再用“模板 + 模型 + 解析器”组成一条链。
- **前置**：0.1（自检通过，`.env` 里有 `DEEPSEEK_API_KEY`）。
- **环境**：调用真实模型。
- **命令**：`python tools/run_chapter.py 1.1`

## 问题

先做一个最小的应用：把一句问题交给模型，显示回复。它像一次普通的接口调用，但返回的是模型根据上下文生成的文字。看清这次往返，后面才能理解提示词、检索和 Agent 各增加了什么。

## 概念

- **模型客户端**：`ChatOpenAI` 保存模型名、地址和密钥。DeepSeek 兼容 OpenAI 的接口格式，所以只需要改 `model` 和 `base_url`。
- **`invoke`**：发起一次调用并等待结果，返回的是消息对象。其中 `.content` 才是要展示的正文，其余是元数据。
- **提示词模板**：`ChatPromptTemplate` 把固定说明（system）和每次变化的问题（human，含 `{question}` 占位符）分开管理。
- **LCEL 链**：`prompt | llm | parser` 里的 `|` 表示左边的输出交给右边作输入；`StrOutputParser` 把消息对象取成字符串。

## 流程

1. 从 `.env` 读取密钥，创建 `llm`。
2. 直接 `llm.invoke("…")`，观察返回的是消息对象，取 `.content`。
3. 定义模板和解析器，用 `|` 连成 `chain`，传入 `{"question": ...}` 调用。

## 代码导读

[first_call.py](first_call.py)：先看 `llm` 和第一次 `invoke`，再看 `prompt`、`parser`、`chain`。本章直接创建 `ChatOpenAI`，让连接配置一眼可见；第 2 篇起统一改用 `common.py` 的 `get_llm()`。

## 练习

1. 先预测直接调用与 chain 调用的返回类型，各运行一次验证。
2. 把 system 改成“你是一个资深测试工程师”，只改这一处，观察回答风格的变化。
3. 用一个错误的 `DEEPSEEK_API_KEY` 环境变量临时运行一次（不要改 `.env`），观察认证错误出现在哪一步。遇到连接或认证错误，先回到 0.1 检查环境，不要先改提示词。

在 [学习记录](workbook.md) 写下预测和实际结果，并记录一次失败情形。

## 运行与边界

- 会调用真实模型并产生少量费用，需要网络和有效的 `DEEPSEEK_API_KEY`。
- 一次成功的回复只能证明调用链可通，不能证明答案正确。
