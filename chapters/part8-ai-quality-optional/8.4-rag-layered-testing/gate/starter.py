"""L3.1 扩展 · RAG 分层检索评测 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/ai_testing/rag_eval.py。实现 evaluate_retrieval，然后运行：

    python chapters/part8-ai-quality-optional/8.4-rag-layered-testing/gate/gate_check.py
"""

from __future__ import annotations


def evaluate_retrieval(cases: list[dict], k: int = 3) -> dict:
    """对每条样本取前 k 个召回（先截取再去重）后求平均。

    返回 recall_at_k/precision_at_k/mrr/citation_coverage。
    - recall = 命中相关来源数 / 全部相关来源；
    - precision = 命中数 / 去重后召回数；
    - MRR = 第一个相关来源排名倒数，未命中 0；
    - citation_coverage = 被引用相关来源 / 全部相关来源；
    - relevant 为空（应拒答）：recall/citation=1.0，precision/MRR=0.0；
    - k<1 -> ValueError；空 cases 全 0。
    """
    raise NotImplementedError("实现检索指标")
