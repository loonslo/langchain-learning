# B5a Gate 验证记录 · 2026-10-18

B5a 只覆盖 5.2 可靠性（5.1 已在样板批次完成）。5.3–5.5、5.7、5.8 仍在 B5 后续批次。

## 范围与结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 5.2 可靠性 | L5.1 | 5 | 5/5 |

默认骨架 0/5（NotImplementedError），退出码 1。

## 回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 271 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check chapters/part5-production/5.2-reliability-retry/gate
All checks passed!
```

## 覆盖的故障

- 指数退避序列/上限截断、max_retries=0、base/max_delay 非法；
- Timeout/Connection 可重试 vs ValueError/KeyError/PermissionError 不可重试；
- 成本公式、usage 缺失/None、负单价。

## 未验证

- 没有真实学习者从零实现；通过的是临时参考解。
- 没有调用真实模型/缓存/tenacity；未验证 jitter、主备切换、缓存失效。
- `reliability.py` 未修改。

## 复现

```bash
python chapters/part5-production/5.2-reliability-retry/gate/gate_check.py
```

默认检查骨架，应 0 通过；实现后可用 `--module 你的实现.py`。

## 边界

- B5 未完成：5.3–5.5、5.7、5.8 待做。
- gate 只验证退避/重试/成本逻辑，真实可靠性未验证。
