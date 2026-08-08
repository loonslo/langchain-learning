# Day51 · 可自由使用的客服 RAG 最小产品

Day51 是 Day51～78 同一个产品的第一个可运行版本，不是一次性 Demo。

## 衔接基线

Day51 没有需要继承的旧产品文件，今天先建立后续三天都要沿用的最小主链：

| 文件 | 状态 | 主链职责 |
|---|---|---|
| `src/customer_support/settings.py` | 新建 | 提供单个知识文件和模型配置 |
| `src/customer_support/knowledge.py` | 新建 | 把 Markdown 转成 chunks 和 Retriever |
| `src/customer_support/bootstrap.py` | 新建 | 组装真实 embedding、Retriever、LLM |
| `src/customer_support/assistant.py` | 新建 | 执行检索、拒答、回答和来源返回 |
| `src/customer_support/app.py` | 新建 | 接收问题并展示结果 |

Day52 起，每天都要在这个基线上标出“新增 / 修改旧文件 / 继承未改”。完整对照见 [`docs/Day51-Day54衔接变更总览.md`](../docs/Day51-Day54衔接变更总览.md)。

## 当天交付

- 用户可以连续输入任意问题，而不是只能运行写死示例。
- 程序先检索真实 FAQ，有证据才调用模型。
- 无证据时在模型调用前拒答。
- 回答来源只取自检索文档 metadata。
- 运行主程序后直接输入问题，不需要记任何参数。

## 真实调用链

```text
用户输入
  → app.py
  → bootstrap.py 创建真实 embedding、Chroma Retriever、LLM
  → CustomerSupportAssistant.ask
  → 检索证据
  → 拒答或生成答案
  → 展示答案和来源
```

## 在 PyCharm 运行

先用 `tools/materialize_day.py` 还原 Day51，然后在 PyCharm 中：

1. 将 `.build/day51/customer-support/src` 标记为 Sources Root。
2. 新建 Python Module 运行配置，Module name 填 `customer_support.app`。
3. Working directory 选择 `.build/day51/customer-support`。
4. 点击运行按钮。

程序中可以连续输入自己的问题，输入 `exit` 或 `退出` 结束。

## 验收

人工验收必须至少尝试一个资料内问题和一个资料外问题。自动测试用于发布前回归，不是用户入口：

在 PyCharm 中右键 `tests` 目录运行全部测试。

Day51 完成后，产品已经能真实问答；它暂时只读取一份 FAQ，Day52 会在同一链路上扩展为多文档。
