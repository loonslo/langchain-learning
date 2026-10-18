# L3.6 回归对比 · Gate（原 3.7）

[全书目录](../../README.md) · [上一章 3.6](../3.6-langsmith-eval/README.md) · [下一章 3.8](../3.8-prompt-ab-judge/README.md)

- **能力**：用同一批样本比较 baseline/candidate 的通过率、引用、拒答、延迟和错误率，并触发回归告警。
- **v2 路径**：L3.6 / 核心（Gate；回归对比）
- **前置**：3.2（指标）、3.5（评测集）。
- **时间盒**：6 小时（1h 读 + 4h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `regression_curve.py`。
- **验收命令**：

```bash
python chapters/part3-evals/3.7-eval-regression-curve/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

“平均分涨了”可能掩盖某类问题全错。回归对比最容易出这些错：

- 基线和候选用了不同题集/配置，比较无意义；
- 只报平均分，不保留失败样本；
- 延迟分位数算错，p99 被最大值或均值替代；
- 告警阈值写反（涨了当降了）；
- 错误率和质量差混为一谈。

这个 gate 用固定 rows/汇总，验证分位数、单条评分、汇总和告警阈值。

## 任务

实现 `gate/starter.py` 的四个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `percentile` | 线性插值分位数；空列表 0；pct 越界报错 |
| `score_case` | keyword/citation/refusal 三项分 + `passed` |
| `summarize` | cases/error_rate/p50/p99/pass_rate/三项均分/failures |
| `regression_alerts` | 5 类退化告警；无退化返回 [] |

关键口径：

- `keyword_score`/`citation_score` 没有对应标注时记 1.0。
- `refusal_ok`：拒答词是否与 `should_refuse` 一致。
- `passed`：keyword ≥0.67、citation ≥0.67、refusal_ok=1。
- 告警：error 上升 >0；p99 上升 >2000ms；pass 下降 >0.02；citation 下降 >0.02；refusal 下降 >0。
- 空 rows -> 全 0，`failures=[]`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 空/单值/插值 | 0 / 自身 / 5 |
| 2 | 正确样本 | 三项满分，passed |
| 3 | 关键词未命中 | score<0.67，failed |
| 4 | 应拒未拒 / 正确拒答 | 0 / 1 |
| 5 | 缺来源 | citation=0，failed |
| 6 | 汇总含异常行 | error_rate=0.5、p50=20、p99=29.8 |
| 7 | 5 类退化 | 5 条告警 |
| 8 | 阈值边界 | 不误报 |

## 验收标准

`gate_check.py` 的 8 项全部 PASS：

- 分位数、正确样本、关键词、拒答、来源、汇总、告警、边界。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么平均分上涨仍可能藏着回归？
2. p99 和均值各适合回答什么问题？
3. 告警阈值应该由谁定？定得太松/太紧的代价？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（8/8）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 3.7 --no-upload
```

对照时只回答：

1. 参考实现的 `score_one` 和你的 `score_case` 阈值一致吗？
2. 参考实现的 `percentile` 和你的实现是否都用线性插值？
3. 参考实现的告警条件里，哪一条最容易误报？

## 概念地图

- **基线与候选**：同一题集、同一配置才有可比性。
- **平均分陷阱**：总分掩盖某类样本的集体退化。
- **分位数**：p50/p99 看尾部延迟，均值看总体。
- **错误率**：只统计运行时异常，不混同质量差。
- **门禁**：阈值是业务风险选择，不是固定真理。

## 边界

- gate 用固定 rows，不调用真实模型。
- 通过 gate 只证明指标/告警逻辑正确，不证明候选版真实退化。
- LangSmith experiment、失败库写出见参考实现与 3.10。
