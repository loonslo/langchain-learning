# B4d Gate 验证记录 · 2026-10-18

B4d 计划 4 项：3.9、4.11、4.12、4.14，现已全部完成。

## 范围与结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 3.9 Agent 轨迹评测 | L4.11 | 7 | 7/7 |
| 4.11 流式与 HITL | L4.7 | 4 | 4/4 |
| 4.12 搜索信任边界 | L4.8 | 5 | 5/5 |
| 4.14 Supervisor 与并行 | L4.10 | 5 | 5/5 |

默认骨架全部 0 通过（NotImplementedError），退出码 1。

## 回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 270 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check <3 个 gate 目录>
All checks passed!
```

## 覆盖的故障

- **3.9**：期望/禁用工具、完成度、步数超限、最少调用、关键词比例、汇总。
- **4.11**：危险动作、金额阈值边界、非法输入、审批输入归一化。
- **4.12**：伪造标签清理、中文/英文注入检测、非字符串输入。
- **4.14**：固定/自定义流水线、未知阶段、非法 pipeline、fan-in 去重保序。

## 未验证

- 没有真实学习者从零实现；通过的是临时参考解。
- 没有调用真实模型/搜索/Tavily；4.11 不跑 interrupt/stream，4.12 不验证模型抗注入。
- 4.14 未跑真实 LangGraph 多 Agent；`trajectory_eval.py`、`streaming_hitl.py`、`tool_safety_search.py`、`langgraph_supervisor.py` 未修改。

## 复现

```bash
python chapters/part3-evals/3.9-agent-trajectory-eval/gate/gate_check.py
python chapters/part4-agents-langgraph/4.11-streaming-hitl/gate/gate_check.py
python chapters/part4-agents-langgraph/4.12-tool-safety-search/gate/gate_check.py
python chapters/part4-agents-langgraph/4.14-supervisor-fanout/gate/gate_check.py
```

## 边界

- B4d 未完成：4.14 多 Agent 待做。
- gate 只验证规则/结构，真实 Agent 行为、HITL 恢复、注入防护未验证。
