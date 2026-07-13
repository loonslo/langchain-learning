# 评测报告目录

这个目录沉淀阶段2的证据链：多数报告由 `evals/` 下的脚本生成，
Day24 的 Prompt A/B 报告由根目录 `day24_prompt_ab_judge.py` 生成。

- `eval_runs.csv`：每次评测的 commit、通过率、延迟、token、成本、失败数。
- `latest_report.md`：最近一次质量评测摘要。
- `failures.json`：失败用例库。
- `prompt_ab_judge_agreement.json`：Prompt A/B 与 judge 一致性结果。
- `agent_trajectory_eval.json`：Agent 工具轨迹评测结果。
- `dashboard.html`：可展示评测看板。

推荐运行顺序（生产级，基于成熟框架 DeepEval）：

```bash
# 1. live 跑评测，产出带真实 retrieval_context 的 failures.json
python -m evals.run_eval_platform --mode live
# 2. 用 DeepEval 对失败 case 算可信维度分，并直接做质量门禁（诊断+门禁一站式）
python day26_eval_report_failures.py --mode live
# 3. 可选：仅做趋势门禁（弱信号守护，无需 key），检测通过率严重回归 / 连续下降
python day26_eval_report_failures.py --input reports/eval_runs.csv
# 4. 看板
python -m evals.dashboard
```

> 说明：原 day27 门禁已合并进 day26。诊断与门禁是同一动作的前后段，一次运行即出结论；
> 真正「接进 CI 自动拦 PR」的部署篇见课程 Day58（capstone/ci_gate.py + .github/workflows/eval-gate.yml）。

框架选型说明（重要）：
- day22–25 的自研硬指标（`refusal_ok`/`keyword_score`/`citation_score`）是**教学练习**：
  测的是字符串包含与措辞格式，测不准语义对错，offline 下还是自证循环。
- day26 切换到**成熟框架**做生产评测。**Ragas 因与当前 langchain 栈存在已知版本冲突已排除**；
  **DeepEval 不依赖 langchain**（实测 4.0.7 仅依赖 openai/pytest 等），零冲突且已就位，故选它。
- day26 的前提：`run_eval_platform --mode live` 已把**真实召回上下文回填**进 `failures.json`。
  没有它，DeepEval 也算不准（这是之前"看不到 deepeval 作用"的根因）。

day26 三段职责：
- 读 `failures.json`（run_eval_platform 的产出），不另造用例。
- 一级：硬指标做「弱信号分流」，结果标注为「疑似 / 待框架复核」——硬指标不可信，只做分组。
- 二级（live）：DeepEval 对失败 case 算真实维度分（Faithfulness/AnswerRelevancy/ContextualPrecision），
  才是可信证据；结论标注为「建议」非「判决」（LLM-as-judge 仍有偶发漏检，如编造）。
- 三级（门禁）：基于二级维度分做发布判决（任一 < 0.7 → 该 case 不通过 → exit(1)），
  另含 `--input` 趋势门禁（弱信号守护）。这是**可信判决**层。
- `--mode live` 需 `DEEPSEEK_API_KEY` + live 产出的 failures.json；offline 仅做结构验证，门禁会阻断发布。
- 退出码：门禁通过=0；未通过=1；数据缺失/用法错误=2。
