"""L3.6 扩展 · Prompt A/B 指标 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
prompt_ab_judge.py。实现下面四个函数，然后运行：

    python chapters/part3-evals/3.8-prompt-ab-judge/gate/gate_check.py
"""

from __future__ import annotations

REFUSE_HINTS = ["没有提到", "信息不足", "无法回答", "不知道", "无相关"]


def normalize(text: str) -> str:
    """小写并去掉所有空白。"""
    raise NotImplementedError("实现归一化")


def looks_refused(answer: str) -> bool:
    """出现任一拒答提示词 -> True。"""
    raise NotImplementedError("实现拒答判断")


def keyword_score(answer: str, keywords: list[str]) -> float:
    """关键词命中比例；无关键词记 1.0。"""
    raise NotImplementedError("实现关键词分")


def citation_score(answer: str, sources: list[str]) -> float:
    """来源命中比例；无来源记 1.0。"""
    raise NotImplementedError("实现引用分")


def refusal_alignment(answer: str, should_refuse: bool) -> float:
    """模型拒答与期望一致记 1.0，否则 0.0。"""
    raise NotImplementedError("实现拒答一致性")
