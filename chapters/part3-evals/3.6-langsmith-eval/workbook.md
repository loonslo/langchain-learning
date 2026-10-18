# L3.6 LangSmith 可观测性 · 清单记录

任务清单见 [gate/CHECKLIST.md](gate/CHECKLIST.md)。本章不提供离线 gate；用真实 trace 和脱敏证据验收。

## 记录

- 日期：
- LangSmith 项目：
- 成功 trace（链接/截图）：
- 三步观察：
  1. retriever：
  2. prompt：
  3. LLM：
- 失败 trace：
  - 失败步骤：
  - 错误信息：
- 在线评估：
  - dataset：
  - experiment：
- 未验证：

## 脱敏检查

- [ ] 没有 `LANGSMITH_API_KEY` / `DEEPSEEK_API_KEY`
- [ ] 没有真实用户问题/PII
- [ ] trace 链接/截图已脱敏

## 边界

- 外部服务，离线环境无法验证。
- trace 可视化不等于质量评测；质量见 3.2–3.5、3.7。
