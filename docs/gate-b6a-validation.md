# B6a Gate 验证记录 · 2026-10-18

B6a 覆盖 6.1 方案选型、8.5 Judge 校准、8.9 CI 分层门禁。其余 B6（8.6、9.x、项目步骤、选修）仍未做。

## 范围与结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 6.1 方案选型 | L5.10 | 6 | 6/6 |
| 8.5 Judge 校准 | L3.4 | 6 | 6/6 |
| 8.9 CI 分层门禁 | L5.7 | 6 | 6/6 |

默认骨架 0/6（NotImplementedError）。

## 回归与结构检查

```text
pytest tools chapters/test_new_lessons.py -q：28 passed
check_course_links：272 个 Markdown，断链 0
apply_v2_map --check：111 unchanged
ruff：All checks passed
```

## 覆盖的故障

- **6.1**：无需求->Prompt、三种检索触发->RAG、微调前提、组合、训练不可行、简化入口。
- **8.5**：阈值标注、并列取小、完全一致、混淆矩阵、kappa=0、空样本。
- **8.9**：全通过、必需层失败、可选层失败、缺层、flaky、空输入。

## 未验证

- 没有真实学习者从零实现；通过的是临时参考解。
- 6.1 不验证真实业务；8.5 用合成分数；8.9 不执行 CI。
- 参考实现未修改。

## 复现

```bash
python chapters/part6-model-tradeoffs/6.1-choose-prompt-rag-finetune/gate/gate_check.py
python chapters/part8-ai-quality-optional/8.5-judge-calibration/gate/gate_check.py
python chapters/part8-ai-quality-optional/8.9-ci-layered-gate/gate/gate_check.py
```

## 边界

- B6 未完成：8.6/9.x/项目步骤/选修待做。
- gate 只验证规则/指标/判定，真实模型和 CI 未验证。
