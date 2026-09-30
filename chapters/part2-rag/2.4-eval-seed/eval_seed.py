"""
章节 2.4 · 评测种子：用固定样本建立评测口径
==========================================================
本文件用确定性的检索和生成替身，演示怎样把"答得对不对"拆成可分别判断的几项。
它不调用 embedding 或 LLM，通过率不代表真实 RAG 的质量。

流程：样本 → 检索替身 → 去重与上下文预算 → 生成替身（作答或拒答） → 分项判断

前置：2.3
运行：python tools/run_chapter.py 2.4（离线）
输出：每个样本的 recall / keyword_ok / refusal_ok / citation_ok / passed；全部通过时退出码为 0
对应测试：python -m pytest chapters/test_new_lessons.py -q
==========================================================
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)  # frozen：片段一旦创建不可修改，避免评测过程中被悄悄改动
class Chunk:
    chunk_id: str   # 片段标识：引用和评测都靠它对齐
    source_id: str  # 来源文件
    topic: str      # 检索替身按主题精确匹配
    text: str


# 两条虚构的客服规则，代替真实知识库
CHUNKS = (
    Chunk("refund-1", "refund.md", "退款", "退款审核通过后3个工作日到账。"),
    Chunk("shipping-1", "shipping.md", "发货", "付款后48小时内发货。"),
)


def load_cases() -> list[dict]:
    """读取样本。样本 ID 必须唯一，否则失败结果无法定位。"""
    cases = json.loads(
        Path(__file__).with_name("seed_cases.json").read_text(encoding="utf-8")
    )
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("评测样本 ID 不得重复")
    return cases


def retrieve(topics: list[str]) -> list[Chunk]:
    """检索替身：主题精确匹配。真实系统用 embedding 或 BM25，这里只为独立验证后面的环节。"""
    return [chunk for chunk in CHUNKS if chunk.topic in topics]


def context(chunks: list[Chunk], max_chars: int = 80) -> list[Chunk]:
    """从召回结果里选出放进上下文的片段：按排名去重，整个片段放不下就跳过。

    保留 chunk_id / source_id，回答才能引用。预算用完时可能出现
    "召回成功但上下文为空"，这是上下文环节的失败，不是检索的失败。
    """
    if max_chars < 0:
        raise ValueError("上下文预算不得为负数")
    selected: list[Chunk] = []
    seen: set[str] = set()
    remaining = max_chars
    for chunk in chunks:
        if chunk.chunk_id in seen:   # 重复片段只保留一次
            continue
        seen.add(chunk.chunk_id)
        if len(chunk.text) <= remaining:
            selected.append(chunk)
            remaining -= len(chunk.text)
    return selected


def generate(chunks: list[Chunk]) -> tuple[str, list[str], bool]:
    """生成替身：返回 (答案, 引用的片段 ID, 是否拒答)。

    有证据就拼接原文作答并引用；没有证据就拒答且不引用。
    """
    if not chunks:
        return "没有足够证据，请联系人工客服。", [], True
    return (
        " ".join(chunk.text for chunk in chunks),
        [chunk.chunk_id for chunk in chunks],
        False,
    )


def evaluate(
    case: dict,
    retrieved: list[Chunk],
    selected: list[Chunk],
    answer: str,
    citations: list[str],
    refused: bool,
) -> dict[str, object]:
    """对一个样本分项判断，只有全部通过才算通过。"""
    expected = set(case["expected_chunks"])
    retrieved_ids = {chunk.chunk_id for chunk in retrieved}
    context_ids = {chunk.chunk_id for chunk in selected}
    actual = set(citations)
    # recall：期望片段被召回了多少；资料外样本没有期望片段，记为 None，不算 100%
    recall = len(expected & retrieved_ids) / len(expected) if expected else None
    # 关键词：粗粒度的正确性检查
    keyword_ok = all(word in answer for word in case["keywords"])
    # 拒答：该答时答，该拒时拒
    refusal_ok = refused == case["should_refuse"]
    # 引用：拒答时不应有引用；作答时必须覆盖期望片段，且都来自上下文（不能编造）
    citation_ok = (
        not actual if refused else bool(actual) and expected <= actual <= context_ids
    )
    passed = (
        refusal_ok and citation_ok and keyword_ok and (recall is None or recall == 1)
    )
    return {
        "id": case["id"],
        "recall": recall,
        "keyword_ok": keyword_ok,
        "refusal_ok": refusal_ok,
        "citation_ok": citation_ok,
        "passed": passed,
    }


def main() -> int:
    reports = []
    for case in load_cases():
        retrieved = retrieve(case["topics"])          # 1 召回
        selected = context(retrieved)                 # 2 选入上下文
        answer, citations, refused = generate(selected)  # 3 生成
        reports.append(evaluate(case, retrieved, selected, answer, citations, refused))  # 4 判断
    print(
        json.dumps(
            {"mode": "offline-fixture", "cases": reports}, ensure_ascii=False, indent=2
        )
    )
    return 0 if all(row["passed"] for row in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
