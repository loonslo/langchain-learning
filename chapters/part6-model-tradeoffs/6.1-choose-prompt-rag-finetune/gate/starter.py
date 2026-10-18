"""L6.1 方案选型 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
model_strategy.py。实现下面两个函数，然后运行：

    python chapters/part6-model-tradeoffs/6.1-choose-prompt-rag-finetune/gate/gate_check.py
"""

from __future__ import annotations


def decide(
    *,
    knowledge_updates_often: bool,
    need_citation: bool,
    model_lacks_required_knowledge: bool,
    need_fixed_behavior: bool,
    enough_training_examples: bool,
    training_is_feasible: bool,
) -> dict:
    """返回 {"strategy","reasons","production_checks"}。

    规则：
    - needs_retrieval = 知识常变 or 需要引用 or 模型缺知识；
    - can_fine_tune = 需要固定行为 and 样本足够 and 训练可行；
    - 两者都真 -> "RAG + 微调"；只检索 -> "RAG"；只微调 -> "微调"；都假 -> "Prompt"；
    - production_checks 至少 3 条；可微调时追加基座对照/许可/回滚检查。
    """
    raise NotImplementedError("实现选型决策")


def recommend(
    knowledge_updates_often: bool,
    need_citation: bool,
    need_fixed_style: bool,
    budget_for_training: bool,
    enough_training_examples: bool = False,
) -> str:
    """简化入口：返回 "策略：理由" 字符串。"""
    raise NotImplementedError("实现简化建议")
