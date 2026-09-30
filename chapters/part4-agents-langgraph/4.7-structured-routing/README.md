# 4.7 结构化路由：把模型选择限制在可验证集合

[全书目录](../../README.md) · [上一章 4.6](../4.6-node-reliability/README.md) · [下一章 4.8](../4.8-plan-and-execute/README.md)

- **目标**：用结构化输出约束模型的路由决策，让分支选择稳定、可测、可断言。
- **前置**：4.6、1.3。
- **环境**：调用真实模型；没配 `DEEPSEEK_API_KEY` 时脚本直接退出。
- **命令**：`python tools/run_chapter.py 4.7`

## 问题

多分支路由常见的写法是：让模型输出自由文本，再用关键词匹配决定去哪。模型多说一句“我建议先 RESEARCH 再 WRITING”，两个关键词就同时命中，路由乱套。用字符串匹配去猜模型的意图，是生产里最脆弱的环节之一。

## 概念

- **结构化输出路由**：用 `PydanticOutputParser` 注入格式说明，再解析，逼模型只返回一个受约束的值（枚举或 JSON）。代码读到的是确定字段，不是需要再解析的文本。
- **`Literal` 枚举**：最省事的强约束，模型只能在给定选项里选，路由函数没有歧义，也能直接断言。
- **兼容性**：DeepSeek 不支持 `with_structured_output` 的 json_schema 模式，`PydanticOutputParser` 兼容任意模型。
- **意图分类分流**：先用一个 `classify` 节点判断问题类型（知识问答 / 数据查询 / 闲聊），再分派到不同的处理节点。这是 RAG、Text2SQL、闲聊按问题类型选工具的通用骨架。
- **代价**：多一次约束（也可能多一次模型调用），换来可测、可复现、不跑偏。

## 流程

`structured_routing.py` 两层：

1. 【一】枚举路由的 Supervisor：`RouteDecision` 规定下一步只能是几个固定值，`route` 直接读字段。
2. 【二】意图分类分流：`Intent` 规定类别（`knowledge`、`data_query`、`chitchat`），`classify` 节点输出分类，`route_intent` 据此分派。

## 代码导读

[structured_routing.py](structured_routing.py)：先看 `RouteDecision` 和 `Intent` 两个 schema，再看 `supervisor`、`classify` 怎样注入格式说明并解析，最后看路由函数为什么可以“零歧义”。

## 练习

1. 学完 4.14 后回来，把 4.14 的固定流水线 Supervisor 改成让模型用 `RouteDecision` 决定下一阶段，并写一个 pytest：喂固定 state，断言路由到预期节点（5.8 讲回归测试）。
2. 给 `Intent` 增加一个类别，观察 `route_intent` 需要改哪里。
3. 故意让模型输出一个不在枚举里的值，观察解析如何失败，以及程序该怎样兜底。

## 运行与边界

- 会调用真实模型并产生费用；结构化约束能降低但不能消除跑偏，仍需要解析失败的兜底。
- 分类结果的正确率要用评测集验证（第 3 篇）。
