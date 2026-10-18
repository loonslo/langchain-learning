# B6h Gate 验证记录 · 2026-10-18

B6h 覆盖 6.2 LoRA 质量门禁、8.4 RAG 分层检索评测、8.10 反馈闭环。

## 结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 6.2 LoRA 门禁 | L6 | 5 | 5/5 |
| 8.4 RAG 分层评测 | L8 | 6 | 6/6 |
| 8.10 反馈闭环 | L3.7 | 5 | 5/5 |

默认骨架 0 通过。

## 回归

```text
pytest tools chapters/test_new_lessons.py -q：28 passed
check_course_links：280 个 Markdown，断链 0
apply_v2_map --check：111 unchanged
ruff：All checks passed
```

## 覆盖

- **6.2**：适配器最低分/相对增益、得分越界、lr/epoch/rank/alpha 校验。
- **8.4**：recall/precision/MRR/citation、拒答样本、k 截断、平均/空集。
- **8.10**：入队去重、字段校验、负反馈审核队列、approve、只导出 approved。

## 未验证

- 临时参考解；不训练 LoRA，不跑真实检索/反馈库。

## 复现

```bash
python chapters/part6-model-tradeoffs/6.2-lora-finetune-optional/gate/gate_check.py
python chapters/part8-ai-quality-optional/8.4-rag-layered-testing/gate/gate_check.py
python chapters/part8-ai-quality-optional/8.10-production-feedback-loop/gate/gate_check.py
```
