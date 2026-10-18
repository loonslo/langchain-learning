# L4.12 Text2SQL 安全门 · Gate 记录

任务书见 [README](README.md)。先预测，再实现，最后填结果；通过 gate 之前不要打开 `text2sql_agent.py`。

## Gate 结果

- 首次运行：x / 4
- FAIL 项与修正：待填写
- 最终：4 / 4
- `gate_report.json`：待填写

## 解释

1. 为什么 SELECT-only 还不够？
2. 表白名单和 LIMIT 为什么必须同时有？
3. 分流错会把什么送进数据库？

## 未验证边界

- 不执行真实 SQL。
- 只读连接/RLS/参数化未验证。
