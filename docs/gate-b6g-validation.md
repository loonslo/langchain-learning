# B6g Gate 验证记录 · 2026-10-18

B6g 覆盖 10.3 A2A JSON-RPC、10.4 跨 Agent 委派。

## 结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 10.3 JSON-RPC 绑定 | L10 | 6 | 6/6 |
| 10.4 跨 Agent 委派 | L10 | 5 | 5/5 |

默认骨架 0 通过。

## 回归

```text
pytest tools chapters/test_new_lessons.py -q：28 passed
check_course_links：279 个 Markdown，断链 0
apply_v2_map --check：111 unchanged
ruff：All checks passed
```

## 覆盖

- **10.3**：send/get/cancel 分发、-32600/-32601/-32602/-32001 错误码、TaskNotFound 优先。
- **10.4**：缺订单号/缺 scope/正常查询、委托 error/input/auth/completed 翻译。

## 未验证

- 临时参考解；未启 FastAPI/HTTP/SSE，未连真实 A2A/订单服务。

## 复现

```bash
python chapters/part10-mcp-a2a-optional/10.3-a2a-protocol-bindings/gate/gate_check.py
python chapters/part10-mcp-a2a-optional/10.4-cross-agent-delegation/gate/gate_check.py
```
