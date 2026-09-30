# 9.4 意图工作流：把理解结果接到业务

[全书目录](../../README.md) · [上一章 9.3](../9.3-stable-json-output/README.md) · [下一章 9.5](../9.5-postgres-rls/README.md)

- **目标**：把 9.1–9.3 的契约接成显式工作流：未知或低置信意图先转人工；缺槽位只追问第一个必要字段；齐全后才进入订单、退款或知识库能力。
- **前置**：9.3（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.4-intent-workflow`，进入 `.build/enterprise/9.4-intent-workflow/enterprise-support` 后运行 `python -m pytest -q`

## 问题

分类与抽取各自能工作，还需要决定何时澄清、何时执行、何时转人工。显式会话状态把这些决定记录下来，让业务路线能被测试。

## 概念

ConversationState 保存意图与槽位；CustomerWorkflow 控制路线；分类器接口允许替换实现。工作流的确定性边界不应被模型自由文本绕开。

## 流程

1. 接收输入并分类（上一轮正在追问槽位时跳过分类，直接当作补充信息）。
2. 意图为 `unknown` 或置信度低于 `MIN_CONFIDENCE`（0.75）时清理状态并转人工。
3. 合并槽位并补参。
4. 齐全后进入对应能力。
5. 结束或转人工时清理适当状态。

## 本章交付

- `workflow.py`：可替换分类器的会话状态机。
- `tests/test_workflow.py`：验证跨轮补参、低置信降级和状态清理。

## 代码导读

workflow.py 先读状态，再读 CustomerWorkflow 的处理方法，对照测试中的跨轮和切换意图。

实现文件：

- [workflow.py](src/enterprise_support/workflow.py)

## 练习

画出缺订单号、低置信与正常齐参三条路线，核对每条的结束和返回状态。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.4-intent-workflow
cd .build/enterprise/9.4-intent-workflow/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

当前工作流建立可测试控制边界，退款等副作用仍需认证、资源归属和审批。

这是业务工作流而非“让 Agent 自主决定一切”。涉及退款、订单、发消息等副作用时，仍应再经过鉴权、只读查询或审批。
