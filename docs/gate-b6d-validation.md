# B6d Gate 验证记录 · 2026-10-18

B6d 覆盖 9.1 few-shot 意图、9.4 意图工作流、9.5 Postgres RLS。

## 范围与结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 9.1 Few-shot 意图 | L9 | 5 | 5/5 |
| 9.4 意图工作流 | L9 | 5 | 5/5 |
| 9.5 Postgres RLS | L5.4 | 4 | 4/4 |

默认骨架 0 通过。

## 回归

```text
pytest tools chapters/test_new_lessons.py -q：28 passed
check_course_links：276 个 Markdown，断链 0
apply_v2_map --check：111 unchanged
ruff：All checks passed
```

## 覆盖

- **9.1**：提示词五类/示例/空问题、str/dict 解析、非法意图/缺字段、confidence 越界。
- **9.4**：低置信/unknown/human 转人工、槽位追问/补齐、补槽不再分类、会话隔离。
- **9.5**：先设租户、SQL 带 tenant/user/session、旧->新、limit 边界、role 校验、commit+close。

## 未验证

- 临时参考解；9.1 不调模型，9.4 用假分类器，9.5 用假连接，未连真实 Postgres/RLS。

## 复现

```bash
python chapters/part9-enterprise-infra-optional/9.1-intent-fewshot/gate/gate_check.py
python chapters/part9-enterprise-infra-optional/9.4-intent-workflow/gate/gate_check.py
python chapters/part9-enterprise-infra-optional/9.5-postgres-rls/gate/gate_check.py
```
