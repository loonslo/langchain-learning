# B3a Gate 验证记录 · 2026-10-18

B3 拆成 B3a（3.1、3.2、3.4、3.5）和 B3b（3.7、3.10 + 3.6 清单）。本记录只覆盖 B3a：新增闭卷骨架、离线验收、README 和 workbook；参考实现未修改。

## 范围

| 章节 | v2 路径 | 验收项 | 新增 |
|---|---|---|---|
| 3.1 失败分析 | L3.1 | 8 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| 3.2 基础评测 | L3.3 | 6 | 同上 |
| 3.4 评测集建设 | L3.2 | 7 | 同上 |
| 3.5 Ragas 与指标口径 | L3.5 | 8 | 同上 |

## 实际执行

### 1. 参考解

| Gate | 结果 |
|---|---|
| 3.1 | 8/8 passed |
| 3.2 | 6/6 passed |
| 3.4 | 7/7 passed |
| 3.5 | 8/8 passed |

### 2. 默认骨架

4 个 gate 用默认 `gate/starter.py` 运行都是 0 通过（`NotImplementedError`），退出码 1。这是预期行为。

### 3. 现有回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 264 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check <4 个 gate 目录>
All checks passed!
```

## 覆盖的故障

| 章节 | 主要故障 |
|---|---|
| 3.1 | 源头/切分/召回/重排/上下文/生成/引用的定位顺序、拒答与引用、缺标注 |
| 3.2 | 应拒未拒、关键词未命中、无关键词跳过、空集、ask_fn 异常、分母 |
| 3.4 | 空集、缺字段、重复 ID、未知题型、类型错、多错误收集、覆盖统计 |
| 3.5 | 合并重复 ID/缺字段、拒答题校验、RAGAS 四列、ask_fn 结果 |

## 未验证

- **没有真实学习者从零实现**：通过的是临时参考解，不是学习记录。
- **没有调用真实模型/LangSmith/RAGAS**：3.2 用假 `ask_fn`；3.5 只准备数据，不跑 RAGAS。
- **没有验证真实评测质量**：指标口径、样本代表性、RAGAS 分数都未验证。
- **没有改参考实现**：`error_analysis.py`、`eval_basics.py`、`dataset_build.py`、`dataset_ragas.py` 均未修改。

## 复现

```bash
python chapters/part3-evals/3.1-error-analysis/gate/gate_check.py
python chapters/part3-evals/3.2-eval-basics/gate/gate_check.py
python chapters/part3-evals/3.4-eval-dataset-build/gate/gate_check.py
python chapters/part3-evals/3.5-eval-dataset-ragas/gate/gate_check.py
```

默认检查骨架，应 0 通过；实现后可用 `--module 你的实现.py`。

## 边界

- B3a 只覆盖 4 章；3.6 是 LangSmith 外部服务，计划用清单验收；3.7/3.10 在 B3b。
- gate 只验证结构/口径，真实评测质量仍要真实模型与评测集。
