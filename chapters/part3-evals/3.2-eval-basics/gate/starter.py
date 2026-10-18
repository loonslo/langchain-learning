"""L3.3 基础评测 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
eval_basics.py。实现下面两个函数，然后运行：

    python chapters/part3-evals/3.2-eval-basics/gate/gate_check.py
"""

from __future__ import annotations

from typing import Callable

REFUSE_HINTS = ["没有提到", "我不知道", "未提及", "无法回答", "未涉及", "找不到", "没有相关"]


def looks_like_refuse(answer: str, hints: list[str] | None = None) -> bool:
    """答案里出现任一拒答提示词即视为拒答；非字符串 -> ValueError。"""
    raise NotImplementedError("实现拒答判断")


def evaluate(
    eval_set: list[dict],
    ask_fn: Callable[[str], str],
    hints: list[str] | None = None,
) -> dict:
    """逐条调用 ask_fn，计算拒答正确率与关键词命中率。

    返回：
    - rows: list[dict]（id/question/answer/refused/error/...）
    - refusal_total, refusal_ok, keyword_total, keyword_ok
    - refusal_accuracy, keyword_accuracy（分母为 0 时 0.0）

    规则：
    - 空评测集 -> 全 0；
    - should_refuse=True 的题只计入拒答指标；
    - 应答题没有 keywords -> 跳过关键词统计；
    - 关键词全部出现才算命中；
    - ask_fn 抛异常：该行记 error、refused=False；仍计入对应分母；
    - 不修改 eval_set。
    """
    raise NotImplementedError("实现基础评测")
