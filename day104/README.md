# Day104 · A2A JSON-RPC、REST 与 SSE 边界

今天把 Day103 的任务模型暴露为 A2A HTTP 边界：JSON-RPC 方法使用 `message/send`、
`tasks/get`、`tasks/cancel`；REST 对应 `/v1/message:send`、`/v1/tasks/{id}`；流式更新用
SSE。方法名与旧版本的 `tasks/send` 不同，不能混用。

## 今日交付

- `a2a_api.py`：JSON-RPC dispatcher、REST/FastAPI factory、SSE event 序列化。
- `tests/test_a2a_api.py`：验证 JSON-RPC 错误、提交/查询/取消和事件格式。

## 今日边界

课程 handler 同步完成小任务；真实长任务应由队列/worker 执行，状态写入持久库，并提供
重连、超时、取消、推送回调和 trace。
