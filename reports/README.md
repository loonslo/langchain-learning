# 报告目录

这里放运行时生成的评测和压测报告；`reports/*.json`、`*.csv`、`*.html` 和 `latest_report.md` 被 `.gitignore` 忽略。当前章节入口见 [章节总地图](../chapters/README.md)。报告文件存在不代表当前模型或版本已经通过验收。

保留的文件都有引用：

- `prompt_ab_judge_agreement.json`：Prompt A/B 与裁判一致性结果，`python -m capstone.interview_evidence --strict-evidence` 把它当作证据文件。
- `loadtest_20260729_234712.json`、`loadtest-20260729-234704-26564-final.json`：2026-07-29 的本地假上游压测（2 用户、5 秒、23 个请求），`capstone/docs/portfolio/` 里引用的数字来自这次。

其余历史输出（评测趋势、失败样本、轨迹、看板、其他压测）已删除，需要时重新运行下面的命令生成。命令从仓库根目录执行：

```bash
# 分项评测口径与失败定位，不调用真实模型
python tools/run_chapter.py 2.4
python tools/run_chapter.py 3.1
# 真实 Prompt A/B：先确认 LangSmith、模型配置与调用范围
python tools/run_chapter.py 3.8
# 整合实现的真实评测与发布门禁
python -m capstone.main eval
python -m capstone.ci_gate
# 本地假上游压测，报告写到本目录
python -m capstone.load_test --fake --users 10 --time 30s
```

章节 3.9 使用合成轨迹，可离线运行以理解评测规则；真实事件轨迹需另行采集。章节 3.7 默认读取 `chapters/shared-data/eval_set_full.json`（先运行 3.4、3.5 生成）；3.10 自带合成样本 `failures_sample.json`，可用 `--input` 换成真实失败样本。真实数据产出与可选依赖需单独核实。历史说明见 [docs/legacy/](../docs/legacy/README.md)。

诊断用于定位错误，发布门禁由 `capstone/ci_gate.py` 和 CI 工作流负责。关键词等硬指标只适合弱信号检查；裁判结论也需校准，不能代替来源、权限和引用边界验证。
