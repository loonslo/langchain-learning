# B4a Gate 验证记录 · 2026-10-18

B4 拆成 B4a（4.1–4.4 控制流基础）、B4b（4.6–4.10）、B4c（4.11、4.12、4.14 + 3.9）。本记录只覆盖 B4a；4.5 已在样板批次完成。

## 范围

| 章节 | v2 路径 | 验收项 | 新增 |
|---|---|---|---|
| 4.1 Agent 模式 | L4.1 | 8 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| 4.2 LangGraph 基础 | L4.2 | 4 | 同上 |
| 4.3 分支与循环 | L4.3 | 4 | 同上 |
| 4.4 状态与 Reducer | L4.3 | 5 | 同上 |

## 实际执行

### 1. 参考解

| Gate | 结果 |
|---|---|
| 4.1 | 8/8 passed |
| 4.2 | 4/4 passed |
| 4.3 | 4/4 passed |
| 4.4 | 5/5 passed |

### 2. 默认骨架

4 个 gate 用默认 `gate/starter.py` 运行都是 0 通过（`NotImplementedError`），退出码 1。这是预期行为。

### 3. 现有回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 267 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check <4 个 gate 目录>
All checks passed!
```

## 覆盖的故障

| 章节 | 主要故障 |
|---|---|
| 4.1 | 非整数参数、预算耗尽、未知工具、planner 异常、工具参数错误 |
| 4.2 | 线性顺序、分支循环、attempts=1 续跑、图状态隔离 |
| 4.3 | improve/route、循环到达标、recursion_limit 防护 |
| 4.4 | 覆盖 vs 累加、滑动窗口、fan-out 无 reducer 报错、三条结果保留 |

## 未验证

- **没有真实学习者从零实现**：通过的是临时参考解，不是学习记录。
- **没有调用真实模型**：4.1/4.3 用脚本化 planner；4.3 后半段真实 Agent 未跑。
- **没有验证检查点/恢复**：4.1 的暂停恢复、4.10 的 checkpoint 未覆盖。
- **没有改参考实现**：`agent_patterns.py`、`linear_graph.py`、`conditional_graph.py`、`branch_loop.py`、`state_reducer.py` 均未修改。

## 复现

```bash
python chapters/part4-agents-langgraph/4.1-agent-patterns/gate/gate_check.py
python chapters/part4-agents-langgraph/4.2-langgraph-basics/gate/gate_check.py
python chapters/part4-agents-langgraph/4.3-branch-loop/gate/gate_check.py
python chapters/part4-agents-langgraph/4.4-state-reducer/gate/gate_check.py
```

默认检查骨架，应 0 通过；实现后可用 `--module 你的实现.py`。

## 边界

- B4a 只覆盖控制流基础；4.6–4.10 在 B4b，4.11/4.12/4.14 + 3.9 在 B4c。
- gate 只验证结构/边界，真实模型规划与恢复未验证。
