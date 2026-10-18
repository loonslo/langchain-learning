# B5b Gate 验证记录 · 2026-10-18

B5b 计划 5 章，现已全部完成：5.3 成本/缓存/路由、5.4 SQLite、5.5 Docker、5.7 安全护栏、5.8 pytest 回归。

## 范围与结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 5.3 成本/缓存/路由 | L5.2 | 4 | 4/4 |
| 5.4 SQLite 持久化 | L5.3 | 4 | 4/4 |
| 5.5 Docker 配置 | L5.7 | 5 | 5/5 |
| 5.7 安全护栏 | L5.5 | 7 | 7/7 |
| 5.8 pytest 回归 | L3.3 | 5 | 5/5 |

默认骨架 0/4、0/7（NotImplementedError），退出码 1。

## 回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 272 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check <2 个 gate 目录>
All checks passed!
```

## 覆盖的故障

- **5.4**：建表/幂等、UTC、trace_id 幂等、游标分页、sources 还原、反馈 rating/外键。
- **5.7**：全角/空格/零宽注入、英文注入、flag/pass 分级、PII 先长后短/同值复用/可还原、日志密钥清洗。

## 未验证

- 没有真实学习者从零实现；通过的是临时参考解。
- 5.4 未验证并发/旧库迁移/WAL 性能；5.7 未调用模型，抗注入/输出审核未验证。
- `sqlite_persistence.py`、`security_guardrails.py` 未修改。

## 复现

```bash
python chapters/part5-production/5.4-sqlite-persistence/gate/gate_check.py
python chapters/part5-production/5.7-security-guardrails/gate/gate_check.py
```

## 边界

- B5b 已完成 5 章；B6 待做。
- gate 只验证结构与纯函数，真实并发/模型安全未验证。
