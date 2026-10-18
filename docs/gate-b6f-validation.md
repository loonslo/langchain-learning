# B6f Gate 验证记录 · 2026-10-18

B6f 覆盖 9.6 只读 SQL、10.1 MCP 授权、10.2 A2A 任务状态机。

## 结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 9.6 只读 SQL | L9 | 6 | 6/6 |
| 10.1 MCP 授权 | L4.9 | 5 | 5/5 |
| 10.2 A2A 任务 | L10 | 5 | 5/5 |

默认骨架 0 通过。

## 回归

```text
pytest tools chapters/test_new_lessons.py -q：28 passed
check_course_links：278 个 Markdown，断链 0
apply_v2_map --check：111 unchanged
ruff：All checks passed
```

## 覆盖

- **9.6**：只读前缀/多语句/禁词/表白名单/LIMIT、目录+角色、EXPLAIN 顺扫阈值。
- **10.1**：audience、scope、高风险审批、检查顺序。
- **10.2**：message_id 幂等、合法/非法/终态迁移、TaskNotFound。

## 未验证

- 临时参考解；未连 Postgres/MCP/A2A 服务。

## 复现

```bash
python chapters/part9-enterprise-infra-optional/9.6-readonly-sql-explain/gate/gate_check.py
python chapters/part10-mcp-a2a-optional/10.1-mcp-auth-approval/gate/gate_check.py
python chapters/part10-mcp-a2a-optional/10.2-a2a-agent-card-task/gate/gate_check.py
```
