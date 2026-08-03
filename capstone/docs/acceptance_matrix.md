# 生产主线验收矩阵

| 能力 | 实际路径 | 最低行为证据 | 运行证据 |
|---|---|---|---|
| 知识回答 | API → AssistantService → KnowledgeBase | 正确拒答、真实引用、实际 API 契约 | 评测报告 |
| 增量摄取 | Connector → Vector Store | 新增/更新/删除、ACL 收紧、失败重试 | 同步 manifest |
| 授权 | JWT → User → 存储过滤 | 跨租户、缺 ACL、角色变化、缓存串号 | 安全测试报告 |
| 上下文 | Authorized hits → Context planner | ACL 在计数/重排前、预算不超限 | context trace |
| 数据工具 | Router → Query catalog → Read-only DB | 未知 query 拒绝、可信身份、超时 | tool trajectory |
| 高风险动作 | AssistantService → ApprovalWorkflow | 重启恢复、重复审批、过期、幂等 | 审批审计 |
| 长期记忆 | Trusted identity → Store | 显式同意、隔离、查看、删除 | memory audit |
| 内容安全 | Input/model/output gateway | 审核器异常失败关闭、正文不进审计 | safety audit |
| Provider | Provider factory → model contract | 配置、错误分类、usage、回归 | provider report |
| 可观测性 | Request path → metrics/log/trace | 成功、失败、取消、样本不足 | SLO 报告 |
| CI | Tests/evals → gate | 质量回归与基础设施错误可区分 | CI artifact |
| 部署 | Image → staging → smoke | 非 root、ready、重启、回滚 | release report |
| 恢复 | Backup → restore → regression | 状态和知识恢复后质量/权限不变 | recovery report |
