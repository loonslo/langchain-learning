"""L3.4 LLM Judge 与校准 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
llm_judge.py。实现下面四个函数，然后运行：

    python chapters/part3-evals/3.3-llm-judge/gate/gate_check.py

不允许为了通过而修改 gate_check.py。
"""

from __future__ import annotations

from typing import Callable

REQUIRED_SAMPLE_KEYS = {"id", "human_pass", "judge_score"}


class JudgeFormatError(ValueError):
    """裁判输出不可解析、分数越界或理由为空。"""


def build_prompt(
    question: str,
    answer: str,
    reference: str,
    context: str,
) -> str:
    """构造裁判 prompt。

    要求：
    - 同时包含 question / answer / reference / context 四项内容；
    - 明确 1–5 分、5 分最好；
    - 明确“只看意思，不纠结措辞”；
    - 明确“答案只能依据上下文，不能编造”。
    """
    raise NotImplementedError("实现裁判 prompt")


def parse_verdict(text: str) -> dict:
    """把裁判输出解析成 {"score": int, "reason": str}。

    要求：
    - 接受纯 JSON，也接受 ```json ... ``` 包裹；
    - 允许 JSON 前后有少量说明文字；
    - score 必须是 1–5 的整数（bool 不算整数）；
    - reason 必须是非空字符串；
    - 任何不合法都抛 JudgeFormatError。
    """
    raise NotImplementedError("实现裁判输出解析")


def judge(
    question: str,
    answer: str,
    reference: str,
    context: str,
    llm_fn: Callable[[str], str],
    attempts: int = 2,
) -> dict:
    """调用裁判并返回 {"score", "reason", "attempts"}。

    要求：
    - 输出不合法或 llm_fn 抛异常时重试，最多 attempts 次；
    - 全部失败抛 JudgeFormatError，错误信息包含最后一次原因；
    - attempts < 1 抛 ValueError。
    """
    raise NotImplementedError("实现带重试的裁判调用")


def calibrate(
    samples: list[dict],
    judge_fn: Callable[[dict], int],
    threshold: int = 4,
) -> dict:
    """用人工标签校准裁判。

    样本字段：{"id": str, "human_pass": bool, "judge_score": int}。
    judge_fn 接收样本，返回 1–5 的整数分数。

    返回：
    - total: int
    - threshold: int
    - agreement: float（预测与人工一致的比例）
    - confusion: {"tp": int, "tn": int, "fp": int, "fn": int}
    - disagreements: list[str]（不一致样本的 id）
    - mean_score: float

    要求：
    - 校验样本字段、ID 唯一、human_pass 为 bool、分数 1–5；
    - 不修改传入的 samples；
    - total=0 时 agreement / mean_score 返回 0.0。
    """
    raise NotImplementedError("实现 Judge 校准")
