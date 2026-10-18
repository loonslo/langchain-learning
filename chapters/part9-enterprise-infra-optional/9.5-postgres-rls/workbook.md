# L5.7 扩展：Postgres 与 RLS · Gate 记录

任务书见 [README](README.md)。先写预测，再实现，最后填结果；通过 gate 之前不要打开 `src/enterprise_support/postgres.py`。

## 闭卷记录

- 开始 / 结束：待填写
- 是否看过参考实现：否
- 实际用时 / 时间盒：待填写 / 5h

## 实现前预测

| 故障注入 | 我预计会发生什么 | 实际结果 | 原因 |
|---|---|---|---|
| limit 0/101 | 待填写 | 待填写 | 待填写 |
| role=system | 待填写 | 待填写 | 待填写 |
| 查询顺序 | 待填写 | 待填写 | 待填写 |
| 未 commit | 待填写 | 待填写 | 待填写 |

## Gate 结果

- 首次运行：x / 4
- FAIL 项与修正：待填写
- 最终：4 / 4
- `gate_report.json`：待填写

## 解释

1. 为什么应用层 WHERE 和 RLS 要同时保留？
2. 为什么查询也要 commit？
3. 为什么游标必须 close？

## 未验证边界

- 假连接，不连真实 Postgres/RLS。
- 事务隔离/连接池未验证。
