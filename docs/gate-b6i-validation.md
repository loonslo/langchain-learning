# B6i 全量收口验证记录 · 2026-10-18

B6i 补齐最后 13 章：7 章 gate + 6 章清单验收。至此 82 章全部有 `gate/gate_check.py` 或 `gate/CHECKLIST.md`。

## 7 个 gate

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 3.8 Prompt A/B 指标 | L3.6 | 5 | 5/5 |
| 4.13 Text2SQL 安全门 | L4.12 | 4 | 4/4 |
| 8.1 风险建模 | L8 | 4 | 4/4 |
| 8.2 评测数据工程 | L8 | 5 | 5/5 |
| 8.3 契约与不变量 | L8 | 5 | 5/5 |
| 8.7 API/SSE E2E | L8 | 5 | 5/5 |
| 8.8 安全/韧性/性能 | L8 | 6 | 6/6 |

默认骨架全部 0 通过。

## 6 个清单

0.1 环境、0.2 学习方法、1.6 MCP 入门、1.7 LLM 原理、4.15 框架取舍、5.6 Ollama；连同 3.6 共 7 个清单验收。

## 覆盖检查

```text
映射章节：82
gate：75
checklist：7
无验收方式：0
```

## 回归

```text
pytest tools chapters/test_new_lessons.py -q：28 passed
check_course_links：见最终检查
apply_v2_map --check：111 unchanged
ruff：All checks passed
```

## 未验证

- 临时参考解；真实模型/搜索/数据库/GPU/外部服务未运行。
- 清单章只提供核对模板，不代表学习者已完成。

## 边界

- 这是课件结构与离线验收的完成，不是学习完成，也不是生产验收。
