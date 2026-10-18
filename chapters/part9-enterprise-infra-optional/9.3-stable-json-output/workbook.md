# L1.3 扩展：稳定 JSON 契约 · Gate 记录

任务书见 [README](README.md)。先写预测，再实现，最后填结果；通过 gate 之前不要打开 `src/enterprise_support/structured_json.py`。

## 闭卷记录

- 开始 / 结束：待填写
- 是否看过参考实现：否
- 实际用时 / 时间盒：待填写 / 4h

## 实现前预测

| 故障注入 | 我预计会发生什么 | 实际结果 | 原因 |
|---|---|---|---|
| 围栏 JSON | 待填写 | 待填写 | 待填写 |
| bool 当 int | 待填写 | 待填写 | 待填写 |
| 多字段 | 待填写 | 待填写 | 待填写 |
| repair 仍坏 | 待填写 | 待填写 | 待填写 |

## Gate 结果

- 首次运行：x / 6
- FAIL 项与修正：待填写
- 最终：6 / 6
- `gate_report.json`：待填写

## 解释

1. 为什么 bool 不能当 int？
2. 为什么 repair 只能一次？
3. allow_extra 适合什么场景？

## 未验证边界

- 不调用模型，只验证解析/校验。
- 真实输出分布/repair prompt 未验证。
