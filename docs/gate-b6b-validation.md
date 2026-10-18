# B6b Gate 验证记录 · 2026-10-18

B6b 覆盖 8.6 轨迹测试、9.7 Redis 缓存/限流、9.12 推理基准；B6 其余项目步骤/选修仍未做。

## 范围与结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 8.6 Agent 轨迹测试 | L4.11 | 6 | 6/6 |
| 9.7 Redis 缓存/限流 | L5.2 | 5 | 5/5 |
| 9.12 推理基准 | L5.8 | 4 | 4/4 |

默认骨架 0 通过（NotImplementedError）。

## 回归与结构检查

```text
pytest tools chapters/test_new_lessons.py -q：28 passed
check_course_links：274 个 Markdown，断链 0
apply_v2_map --check：111 unchanged
ruff：All checks passed
```

## 覆盖的故障

- **8.6**：工具白名单、写工具审批、编号连续、最大步数、未知动作。
- **9.7**：作用域键隔离、空白归一化、bytes 解码、TTL、固定窗口限流、后端故障失败关闭。
- **9.12**：nearest-rank p95、只统计成功样本、错误率分母、空/无成功样本、SLO。

## 未验证

- 没有真实学习者从零实现；通过的是临时参考解。
- 9.7 用假 Redis，未验证 Lua 原子性/真实 Redis；9.12 用合成样本。
- 参考实现未修改。

## 复现

```bash
python chapters/part8-ai-quality-optional/8.6-agent-trajectory-testing/gate/gate_check.py
python chapters/part9-enterprise-infra-optional/9.7-redis-cache-ratelimit/gate/gate_check.py
python chapters/part9-enterprise-infra-optional/9.12-inference-benchmark/gate/gate_check.py
```

## 边界

- B6 未完成：项目步骤、9.x 其余、10.x 选修待做。
- gate 只验证策略/缓存/统计，真实服务未验证。
