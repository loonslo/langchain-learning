# L9 只读 SQL 护栏 · Gate 记录

任务书见 [README](README.md)。先预测，再实现，最后填结果；通过 gate 之前不要打开 `src/enterprise_support/sql_guard.py`。

## Gate 结果

- 首次运行：x / 6
- FAIL 项与修正：待填写
- 最终：6 / 6
- `gate_report.json`：待填写

## 解释

1. 关键词防线为什么不够？
2. 为什么必须有 LIMIT？
3. 查询目录比让 Agent 写 SQL 好在哪？

## 未验证边界

- 不连接真实 Postgres，不执行 SQL。
- 关键词可被绕过。
