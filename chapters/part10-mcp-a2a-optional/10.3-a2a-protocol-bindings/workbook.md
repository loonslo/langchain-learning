# L10 A2A JSON-RPC 绑定 · Gate 记录

任务书见 [README](README.md)。先预测，再实现，最后填结果；通过 gate 之前不要打开 `src/enterprise_support/a2a_api.py`。

## Gate 结果

- 首次运行：x / 6
- FAIL 项与修正：待填写
- 最终：6 / 6
- `gate_report.json`：待填写

## 解释

1. 为什么 TaskNotFound 要先于 KeyError 捕获？
2. 错误码为什么必须稳定？
3. params 非对象为什么不能继续？

## 未验证边界

- 不启 FastAPI/HTTP/SSE，只验证分发。
- 真实 A2A 传输未接入。
