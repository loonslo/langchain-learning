# L5.10 方案选型 · Gate（原 6.1）

[全书目录](../../README.md) · [上一章 5.8](../../part5-production/5.8-pytest-regression/README.md) · [下一章 6.2](../6.2-lora-finetune-optional/README.md)

- **能力**：按知识/引用/行为/样本/训练条件，选择 Prompt、RAG、微调或组合，并给出上线检查项。
- **v2 路径**：L5.10 / 核心（Gate；方案选型）
- **前置**：2.3（RAG）、1.3（结构化输出）。
- **时间盒**：4 小时（1h 读 + 2h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `model_strategy.py`。
- **验收命令**：

```bash
python chapters/part6-model-tradeoffs/6.1-choose-prompt-rag-finetune/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

选型最常见的错误是套口诀：

- 知识常变/要引用/模型不掌握，却只改 Prompt；
- 需要固定行为，但样本不足/训练不可行，却硬上微调；
- 把微调当动态知识库；
- 只给方案，不给上线前检查项。

这个 gate 用需求约束组合，验证四种起始方案和检查项。

## 任务

实现 `gate/starter.py` 的 `decide` 和 `recommend`：

| 函数 | 你要交付的行为 |
|---|---|
| `decide` | 检索需求/微调前提 -> Prompt/RAG/微调/组合；返回 reasons + checks |
| `recommend` | 简化入口，返回 `"策略：理由"` |

关键口径：

- `needs_retrieval = 知识常变 or 需要引用 or 模型缺知识`。
- `can_fine_tune = 需要固定行为 and 样本足够 and 训练可行`。
- 两者都真 -> `RAG + 微调`；只检索 -> `RAG`；只微调 -> `微调`；都假 -> `Prompt`。
- `production_checks` 至少 3 条；可微调时追加基座对照/许可/回滚。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 全部 False | Prompt |
| 2 | 三种检索条件任一 True | RAG |
| 3 | 固定行为+样本+训练可行 | 微调 + 基座检查 |
| 4 | 检索+微调都满足 | RAG + 微调 |
| 5 | 训练不可行 | 不选微调 |
| 6 | 简化入口 | `RAG：...` / `微调：...` |

## 验收标准

`gate_check.py` 的 6 项全部 PASS；通过后写 workbook 三个问题。

## 边界

- gate 只验证选型规则，不证明方案在真实业务有效。
- 通过 gate 不替代离线评测/线上观测。
