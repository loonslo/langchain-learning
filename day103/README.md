# Day103 · A2A Agent Card、任务生命周期与幂等

A2A 不是把多个 LangGraph 节点放在一起，而是让独立 Agent 通过能力卡和任务协议协作。
今天实现 Agent Card、任务状态机与 message id 幂等：网络重试不能创建两个退款/订单任务。

## 今日交付

- `a2a.py`：Agent Card、Task 状态、任务仓储和合法状态迁移。
- `tests/test_a2a.py`：验证公开能力不带密钥、同一 messageId 幂等、终态无法重启。

## 今日边界

内存仓储仅用于离线学习。跨进程 A2A 服务必须把任务、去重键、审计事件落在持久化存储，
并用认证身份决定租户与授权范围。
