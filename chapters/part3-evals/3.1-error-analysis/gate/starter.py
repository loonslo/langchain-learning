"""L3.1 失败分析 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
error_analysis.py。实现 diagnose，然后运行：

    python chapters/part3-evals/3.1-error-analysis/gate/gate_check.py
"""

from __future__ import annotations


def diagnose(trace: dict) -> tuple[str, str]:
    """按管线顺序报告“最先失败的环节”，返回 (环节, 下一步检查)。

    trace 字段：
    - case_id, source_available, chunk_contains_fact
    - expected_ids / retrieved_ids / ranked_ids / context_ids / cited_ids
    - answer_correct, should_refuse, refused

    判定顺序：
    1. should_refuse：未拒答 -> refusal；拒答但带引用 -> citation；否则 pass；
    2. 资料内样本没有 expected_ids -> labeling；
    3. source_available=False -> source；
    4. chunk_contains_fact=False -> chunking；
    5. expected 不在 retrieved_ids -> retrieval；
    6. expected 不在 ranked_ids -> reranking；
    7. expected 不在 context_ids -> context；
    8. refused 或 answer_correct=False -> generation；
    9. cited_ids 不覆盖 expected，或引用了 context 外的 ID -> citation；
    10. 否则 pass。
    """
    raise NotImplementedError("实现失败定位")
