# L4.9 MCP 授权与审批 · Gate 记录

任务书见 [README](README.md)。先预测，再实现，最后填结果；通过 gate 之前不要打开 `src/enterprise_support/mcp_auth.py`。

## Gate 结果

- 首次运行：x / 5
- FAIL 项与修正：待填写
- 最终：5 / 5
- `gate_report.json`：待填写

## 解释

1. 为什么 audience 必须先于 scope/审批检查？
2. 高风险工具为什么必须审批？
3. 为什么身份以 claims 为准？

## 未验证边界

- 不验证签名/真实 IdP。
- 真实 MCP server 未连接。
