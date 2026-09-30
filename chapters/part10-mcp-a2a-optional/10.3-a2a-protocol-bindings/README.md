# 10.3 A2A HTTP 边界：协议形状和任务语义一起校验

[全书目录](../../README.md) · [上一章 10.2](../10.2-a2a-agent-card-task/README.md) · [下一章 10.4](../10.4-cross-agent-delegation/README.md)

- **目标**：把 10.2 的任务模型暴露为 A2A HTTP 接口：JSON-RPC（`message/send`、`tasks/get`、`tasks/cancel`）、REST（`/v1/message:send`、`/v1/tasks/{id}`）和 SSE；旧版 `tasks/send` 不能混用。
- **前置**：10.2（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 10.3-a2a-protocol-bindings`，进入 `.build/enterprise/10.3-a2a-protocol-bindings/enterprise-support` 后运行 `python -m pytest -q`

## 问题

有了任务状态后，还需要客户端能通过 HTTP 提交、查询和取消，并接收流式更新。方法名、错误形状和事件序列都属于需要验证的接口。

## 概念

JSON-RPC 用方法调用包装请求；REST 用资源路径交互；SSE 交付事件。它们共享任务模型，不能各自生成相互矛盾的状态。

## 流程

1. 解析提交请求。
2. A2AApplication 处理任务。
3. 返回结果或标准错误。
4. 查询和取消读取同一任务（REST 只提供查询，取消走 JSON-RPC 的 `tasks/cancel`）。
5. `/v1/message:stream` 把任务快照编码成一帧 SSE（本章任务同步完成，不是增量推送）。

## 本章交付

- `a2a_api.py`：JSON-RPC dispatcher、REST/FastAPI factory、SSE event 序列化。
- `tests/test_a2a_api.py`：验证 JSON-RPC 错误码（含任务不存在）、提交/查询和事件格式。

## 代码导读

a2a_api.py 先读 AgentOutcome 与 A2AApplication，再读 create_fastapi_app 的路由和错误映射；以本章实现的协议范围为准。

实现文件：

- [a2a_api.py](src/enterprise_support/a2a_api.py)

## 练习

用测试客户端验证提交后查询与取消，再观察非法方法和缺任务标识的错误。核对流式状态是否与查询一致。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 10.3-a2a-protocol-bindings
cd .build/enterprise/10.3-a2a-protocol-bindings/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

这里实现的是有限协议边界，不代表全版本兼容认证；远端互操作需与双方当前实现独立验收。

课程 handler 同步完成小任务；真实长任务应由队列/worker 执行，状态写入持久库，并提供重连、超时、取消、推送回调和 trace。
