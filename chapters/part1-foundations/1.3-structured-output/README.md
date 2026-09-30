# 1.3 结构化输出：让程序读懂模型的回答

[全书目录](../../README.md) · [上一章 1.2](../1.2-control-output/README.md) · [下一章 1.4](../1.4-context-memory/README.md)

- **目标**：让模型按 Pydantic 定义的结构返回数据，程序直接取字段使用。
- **前置**：1.1。
- **环境**：调用真实模型。
- **命令**：`python tools/run_chapter.py 1.3`

## 问题

前两章模型返回的是一段话，人能读，程序不好用：要取评分、判断情感、写入数据库，都得先从文字里抠信息。让模型直接返回带字段的对象，就能 `result.score` 取值、做断言，这也是后面自动评测的前提。

## 概念

- **Pydantic 模型**：用一个 `BaseModel` 类声明字段名和类型。`Field(description=...)` 的说明会传给模型，相当于告诉它每个字段该填什么。
- **`with_structured_output`**：把模型类交给 LLM，得到的链直接产出该类的对象（不是字典，用 `.score` 取值）。底层通过 function calling 约束输出，比“要求模型输出 JSON，再自己解析”更稳。
- **类型只约束格式**：字段齐全、类型正确，不代表内容正确。评分是否合理、情感判断是否对，仍要另行验证。

## 流程

1. 定义 `CodeReview`（总结、问题列表、评分）。
2. 用 `llm.with_structured_output(CodeReview, method="function_calling")` 得到结构化模型，接进 `prompt | structured_llm`。
3. 调用后直接读取 `.summary`、`.issues`、`.score`。
4. 换成 `SentimentResult` 结构，批量分析三条文本，观察每条的情感、置信度和关键词。

## 代码导读

[structured_output.py](structured_output.py)：先看 `CodeReview` 类和 `Field` 说明，再看 `with_structured_output` 之后的调用与取值。第二个例子是同一模式换字段，重点比较字段说明怎样影响模型填值。

## 练习

1. 定义 `BugReport`（标题、严重级别、复现步骤），让模型从一段缺陷描述里抽取出结构化缺陷单。
2. 把 `score` 的说明改成“0–100 的整数”，观察输出如何变化。
3. 给出与字段无关的输入，观察模型如何填充；思考失败时程序该怎么处理（拒绝、重试或人工确认）。

## 运行与边界

- 会调用真实模型并产生少量费用。
- 少数模型的 function calling 支持不稳；报错时可退回 `JsonOutputParser` 或换模型。
- 结构合法不等于答案正确，程序仍要校验取值范围和业务规则。
