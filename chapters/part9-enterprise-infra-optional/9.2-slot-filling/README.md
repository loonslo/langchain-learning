# 9.2 槽位与追问：只补真正缺少的信息

[全书目录](../../README.md) · [上一章 9.1](../9.1-intent-fewshot/README.md) · [下一章 9.3](../9.3-stable-json-output/README.md)

- **目标**：显式保存槽位状态，只在缺必填信息时追问；意图只决定走哪条业务线，退款仍必须有订单号。
- **前置**：9.1（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.2-slot-filling`，进入 `.build/enterprise/9.2-slot-filling/enterprise-support` 后运行 `python -m pytest -q`

## 问题

用户说我要查订单，系统还缺订单号。下一轮给了订单号以后，不能再次从头问。槽位状态帮助应用跨轮保存已获得的信息。

## 概念

槽位是完成业务所需字段；SlotState 保存当前值；缺参判断决定下一次追问。提取出一个编号不代表该用户有权访问这个订单。

## 流程

1. extract_slots 提取本轮信息。
2. resolve_slots 与历史合并。
3. 根据意图检查必填字段。
4. next_question 只询问必要缺项。

## 本章交付

- `slots.py`：订单号抽取、槽位合并、缺参提示。
- `tests/test_slots.py`：验证跨轮补参和不同意图的槽位边界。

## 代码导读

slots.py 按提取、合并、追问顺序阅读，核对切换意图时哪些字段应继续保留。

实现文件：

- [slots.py](src/enterprise_support/slots.py)

## 练习

设计两轮补参和一次中途换意图的对话，预测每轮状态与追问；检查已经填写的信息是否被误覆盖。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.2-slot-filling
cd .build/enterprise/9.2-slot-filling/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

当前是规则提取基线；替换为模型提取仍应复用同一契约并验证跨会话隔离。

规则抽取用于建立可测试基线；上线时可替换为 LLM schema 抽取，但仍必须复用同一 `SlotState` 契约和缺参校验。
