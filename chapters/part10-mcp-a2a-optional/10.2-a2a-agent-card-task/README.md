# 10.2 A2A 任务生命周期：远端协作需要可追踪状态

[全书目录](../../README.md) · [上一章 10.1](../10.1-mcp-auth-approval/README.md) · [下一章 10.3](../10.3-a2a-protocol-bindings/README.md)

- **目标**：用 Agent Card 和任务协议让独立 Agent 协作：实现任务状态机和 message id 幂等，网络重试不能创建两个退款或订单任务。
- **前置**：10.1（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 10.2-a2a-agent-card-task`，进入 `.build/enterprise/10.2-a2a-agent-card-task/enterprise-support` 后运行 `python -m pytest -q`

## 问题

独立 Agent 接收任务后可能需要补充输入，也可能被取消。网络重试还可能重复发送同一消息。任务状态和幂等标识让双方知道工作进行到哪里。

## 概念

Agent Card 描述公开能力；AgentTask 保存任务状态；messageId 帮助识别重复请求；合法迁移限制状态变化。

```text
submitted        → working / canceled / rejected / auth-required
working          → input-required / auth-required / completed / canceled / failed
input-required、auth-required → working / canceled / failed
completed、canceled、failed、rejected 是终态，不能再迁移
```

## 流程

1. 读取能力卡。
2. 创建或复用任务。
3. 按工作进展转换状态。
4. 缺输入时进入 `input-required`（本章没有实现“补充输入后继续同一任务”，练习可以扩展）。
5. 完成或取消进入终态。

## 本章交付

- `a2a.py`：Agent Card、Task 状态、任务仓储和合法状态迁移。
- `tests/test_a2a.py`：验证公开能力不带密钥、同一 messageId 幂等、处理中可要求认证、终态无法重启。

## 代码导读

a2a.py 先读 TaskState、AgentCard 与 AgentTask，再读 InMemoryTaskStore 的幂等和迁移规则。

实现文件：

- [a2a.py](src/enterprise_support/a2a.py)

## 练习

重复提交同一个消息标识，预测任务数量；尝试从终态继续执行，解释为何应拒绝。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 10.2-a2a-agent-card-task
cd .build/enterprise/10.2-a2a-agent-card-task/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

本章为本机任务模型；真实跨网络身份、持久化和恢复需要另行验证，能力卡也不应包含秘密。

内存仓储仅用于离线学习。跨进程 A2A 服务必须把任务、去重键、审计事件落在持久化存储，并用认证身份决定租户与授权范围。
