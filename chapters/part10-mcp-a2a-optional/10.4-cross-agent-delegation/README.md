# 10.4 跨 Agent 集成：把委托落到受控订单读取

[全书目录](../../README.md) · [上一章 10.3](../10.3-a2a-protocol-bindings/README.md)

- **目标**：完成最小跨 Agent 场景：客服 Agent 委托订单 A2A Agent 查订单；缺订单号返回 `input-required`，缺权限返回 `auth-required`，否则经已授权的读取器返回结果。
- **前置**：10.3（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 10.4-cross-agent-delegation`，进入 `.build/enterprise/10.4-cross-agent-delegation/enterprise-support` 后运行 `python -m pytest -q`

## 问题

最后用一个小而完整的场景收束：客服 Agent 识别订单需求，委托订单 Agent 处理，订单结果经过受控读取器返回。重点是委托上下文和缺参行为如何贯穿两端。

## 概念

DelegationContext 承载受控身份范围；订单 Agent 处理自己的任务；MCP 用于工具接入，A2A 用于独立 Agent 协作。职责分开才能解释授权和失败位置。

## 流程

1. 客服端把用户原话和委托上下文发给订单 Agent。
2. 订单 Agent 提取订单号：缺订单号返回 `input-required`，缺 `orders.read` 返回 `auth-required`。
3. 齐参后经 OrderReader 读取。
4. 结果回到客服端。
5. 验收覆盖正常、缺参和越权。

## 本章交付

- `integration.py`：订单 Agent、A2A 客户端适配器和不带密钥的委托上下文。
- `acceptance.py`：离线验收四条关键链路：意图与槽位、JSON 契约、Qdrant 租户过滤、A2A 委托。
- `PROJECT_README.md`：章节 9.1–10.4 可交付能力、运行与边界。

## 代码导读

integration.py 先读 DelegationContext 与 OrderReader，再读 OrderAgent 和 SupportOrderDelegator；acceptance.py 提供离线整合入口。

实现文件：

- [acceptance.py](src/enterprise_support/acceptance.py)
- [integration.py](src/enterprise_support/integration.py)

## 练习

用正常订单、缺订单号和无访问权限三种输入画出路线，再运行累积验收并记录对应证据。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 10.4-cross-agent-delegation
cd .build/enterprise/10.4-cross-agent-delegation/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

InProcessA2AClient 是进程内测试边界，当前结果不代表真实远端 Agent 或企业工具已经联调通过。委托上下文的 `as_metadata()` 会随消息发送，但订单 Agent 不读取它：身份和 scope 在构造 `OrderAgent` 时传入。真实系统必须由订单端用认证令牌确定身份，不能信任请求里自称的 tenant 或 scope。

你现在有一个可运行、可测的企业 Agent 进阶项目骨架；仍不要声称已经完成 Kubernetes/ACK、高可用发布、企业 IdP 对接、真实 GPU 容量压测或生产 A2A 联调。这些需要在明确目标环境后继续深化。
