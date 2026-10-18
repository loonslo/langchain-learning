# B3b Gate 验证记录 · 2026-10-18

B3b 覆盖 3.7、3.10 两个离线 gate，以及 3.6 的清单验收（LangSmith 外部服务）。B3a 见 [gate-b3a-validation.md](gate-b3a-validation.md)。

## 范围

| 章节 | v2 路径 | 验收方式 | 新增 |
|---|---|---|---|
| 3.6 LangSmith | L3.6 | 清单（无离线 gate） | `gate/CHECKLIST.md`、README 说明、workbook 模板 |
| 3.7 回归对比 | L3.6 | 8 项离线 gate | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| 3.10 失败诊断 | L3.6 扩展 | 5 项离线 gate | 同上 |

## 实际执行

### 1. 参考解

| Gate | 结果 |
|---|---|
| 3.7 | 8/8 passed |
| 3.10 | 5/5 passed |

### 2. 默认骨架

2 个 gate 用默认 `gate/starter.py` 运行都是 0 通过（`NotImplementedError`），退出码 1。这是预期行为。

### 3. 现有回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 266 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check chapters/part3-evals/3.7-eval-regression-curve/gate ...
All checks passed!
```

## 覆盖的故障

| 章节 | 主要故障 |
|---|---|
| 3.7 | 分位数空/单值/插值、关键词/引用/拒答评分、异常行汇总、5 类告警、阈值边界 |
| 3.10 | 缺/坏失败库、passed 过滤、live/offline 推断、分组顺序、层统计 |

## 3.6 清单

3.6 依赖 LangSmith 外部服务，没有可重复的离线 gate。清单要求：

- 一条成功 trace 的链接/截图；
- 能指出 retriever / prompt / LLM 三步；
- 一条失败 trace 和失败步骤；
- 在线评估 dataset/experiment（无 key 时明确写未验证）；
- 证据不含密钥/真实用户 PII。

清单见 `chapters/part3-evals/3.6-langsmith-eval/gate/CHECKLIST.md`；本次未执行真实 LangSmith 验证。

## 未验证

- **没有真实学习者从零实现**：通过的是临时参考解，不是学习记录。
- **没有调用真实模型/LangSmith/DeepEval**：3.7 用固定 rows；3.10 只做一级分流。
- **没有验证真实回归/根因**：指标与分组逻辑正确，不代表真实系统退化或根因判断准确。
- **没有改参考实现**：`regression_curve.py`、`failure_diagnosis.py` 均未修改。

## 复现

```bash
python chapters/part3-evals/3.7-eval-regression-curve/gate/gate_check.py
python chapters/part3-evals/3.10-eval-report-failures/gate/gate_check.py
```

默认检查骨架，应 0 通过；实现后可用 `--module 你的实现.py`。

## 边界

- B3 完成：3.1–3.5、3.7、3.10 gate；3.6 清单；3.8/3.9 仍待后续。
- 下一批 B4 是 L4 Agent 的 12 章，未开始。
