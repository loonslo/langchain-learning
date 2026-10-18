# B4b Gate 验证记录 · 2026-10-18

B4b 覆盖 4.6 节点可靠性、4.7 结构化路由。原计划的 4.8–4.10 移到 B4c，避免一批过大。B4a 见 [gate-b4a-validation.md](gate-b4a-validation.md)。

## 范围

| 章节 | v2 路径 | 验收项 | 新增 |
|---|---|---|---|
| 4.6 节点可靠性 | L4.3 扩展 | 7 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| 4.7 结构化路由 | L4.5 | 4 | 同上 |

## 实际执行

### 1. 参考解

| Gate | 结果 |
|---|---|
| 4.6 | 7/7 passed |
| 4.7 | 4/4 passed |

### 2. 默认骨架

2 个 gate 用默认 `gate/starter.py` 运行都是 0 通过（`NotImplementedError`），退出码 1。

### 3. 现有回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 268 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check <2 个 gate 目录>
All checks passed!
```

## 覆盖的故障

| 章节 | 主要故障 |
|---|---|
| 4.6 | 成功/降级、可重试判断、真实超时、非法 seconds、fn 异常透传 |
| 4.7 | 非法 JSON/缺字段/非法枚举、done 路由、非法 `_next`、未知意图 |

## 未验证

- **没有真实学习者从零实现**：通过的是临时参考解，不是学习记录。
- **没有调用真实模型**：4.6 用假函数/真 sleep；4.7 用固定 JSON。
- **没有验证 RetryPolicy/ToolNode**：4.6 的框架重试与工具错误回喂未跑。
- **没有改参考实现**：`node_reliability.py`、`structured_routing.py` 均未修改。

## 复现

```bash
python chapters/part4-agents-langgraph/4.6-node-reliability/gate/gate_check.py
python chapters/part4-agents-langgraph/4.7-structured-routing/gate/gate_check.py
```

默认检查骨架，应 0 通过；实现后可用 `--module 你的实现.py`。

## 边界

- B4b 只覆盖 2 章；4.8–4.10、4.11/4.12/4.14 + 3.9 在 B4c。
- gate 只验证结构/边界，真实模型限流、路由准确率未验证。
