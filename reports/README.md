# 评测报告目录

这个目录由 `evals/` 下的脚本生成，用来沉淀阶段2的证据链：

- `eval_runs.csv`：每次评测的 commit、通过率、延迟、token、成本、失败数。
- `latest_report.md`：最近一次质量评测摘要。
- `failures.json`：失败用例库。
- `prompt_ab_judge_agreement.json`：Prompt A/B 与 judge 一致性结果。
- `agent_trajectory_eval.json`：Agent 工具轨迹评测结果。
- `dashboard.html`：可展示评测看板。

推荐运行顺序：

```bash
python -m evals.run_eval_platform
python -m evals.prompt_ab_judge_agreement
python -m evals.agent_trajectory_eval
python -m evals.dashboard
```
