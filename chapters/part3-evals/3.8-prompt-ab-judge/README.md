# L3.6 扩展：Prompt A/B 指标 · Gate（原 3.8）

[全书目录](../../README.md) · [上一章 3.7](../3.7-eval-regression-curve/README.md) · [下一章 3.9](../3.9-agent-trajectory-eval/README.md)

- **能力**：归一化答案；判拒答；关键词/引用命中率；拒答一致性。
- **v2 路径**：L3.6 / 核心（Gate；Prompt A/B 指标）
- **前置**：3.2（指标）。
- **时间盒**：4 小时。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `prompt_ab_judge.py`。
- **验收命令**：

```bash
python chapters/part3-evals/3.8-prompt-ab-judge/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

A/B 选 prompt 不能靠感觉：全角/空白导致关键词误判、拒答词漏配、无关键词/无来源时除零、误拒答被算通过。

## 任务

实现 `normalize`、`looks_refused`、`keyword_score`、`citation_score`、`refusal_alignment`：

| 指标 | 口径 |
|---|---|
| keyword | 命中关键词/全部；无关键词 1.0 |
| citation | 命中来源/全部；无来源 1.0 |
| refusal | 实际拒答==期望 -> 1，否则 0 |

关键口径：`normalize` 小写并去所有空白。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 全角/空格 | 归一化后匹配 |
| 2 | “信息不足” | refused=True |
| 3 | 关键词 2 中 1 | 0.5 |
| 4 | 无关键词/无来源 | 1.0 |
| 5 | 误拒答/正常答案 | 0/1 |

## 验收标准

`gate_check.py` 的 5 项全部 PASS；通过后写 workbook 三个问题。

## 边界

- 不调用模型/LangSmith，只算指标。
- 真实 A/B 结论需真实运行与评测集。
