"""L2.9 RAG 评测基线 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
eval_seed.py。实现下面四个函数，然后运行：

    python chapters/part2-rag/2.4-eval-seed/gate/gate_check.py

不允许为了通过而修改 gate_check.py 或 cases.json。
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

REQUIRED_CASE_KEYS = {
    "id",
    "question",
    "expected_chunks",
    "keywords",
    "should_refuse",
}
REQUIRED_RESULT_KEYS = {"answer", "sources", "refused", "retrieved_ids"}


def load_cases(path: str | Path) -> list[dict]:
    """读取评测样本并校验契约。

    要求：
    - 返回 JSON 数组，元素是 dict；
    - 每个样本包含 REQUIRED_CASE_KEYS 的全部字段；
    - id 必须唯一；
    - 校验失败抛 ValueError，不要静默跳过。
    """
    raise NotImplementedError("实现样本加载与校验")


def evaluate_case(case: dict, result: dict) -> dict:
    """判断一条 RAG 结果，返回分项结果。

    result 形状：
        {"answer": str, "sources": list[str], "refused": bool,
         "retrieved_ids": list[str]}

    sources 是片段 ID（如 "refund-1"），不是文件名。
    返回字段：
    - id: str
    - retrieval_hit: bool | None；expected_chunks 为空时为 None
    - citation_ok: bool
    - refusal_ok: bool
    - keyword_ok: bool
    - passed: bool

    判定口径：
    - retrieval_hit：expected_chunks 是否全部出现在 retrieved_ids；
    - citation_ok：拒答时 sources 必须为空；作答时 sources 非空、
      覆盖全部 expected_chunks，且是 retrieved_ids 的子集、无重复；
    - refusal_ok：refused 是否等于 should_refuse；
    - keyword_ok：keywords 是否全部出现在 answer；
    - passed：以上四项全部成立（retrieval_hit 为 None 时不参与）。
    """
    raise NotImplementedError("实现单条评测")


def summarize(rows: list[dict]) -> dict:
    """汇总分项结果。

    返回字段：
    - total: int
    - passed: int
    - pass_rate: float
    - retrieval_hit_rate: float | None；没有任何带期望片段的样本时为 None
    - citation_accuracy: float
    - refusal_accuracy: float

    分母为 0 时返回 0.0；不要用 round 改变精度（gate 会自己比较）。
    """
    raise NotImplementedError("实现汇总")


def run(cases: list[dict], ask_fn: Callable[[str], dict]) -> dict:
    """对每条样本调用 ask_fn，再评测并汇总。

    返回 {"rows": [...], "summary": {...}}。
    要求：
    - ask_fn 接收 question，返回 result 形状；
    - 不修改传入的 cases；
    - ask_fn 抛异常时，该行标记 passed=False、error=可读字符串，
      不要让整批评测中断。
    """
    raise NotImplementedError("实现评测运行器")
