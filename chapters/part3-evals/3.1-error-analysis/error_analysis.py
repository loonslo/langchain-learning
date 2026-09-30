"""
章节 3.1 · 失败分析：先找到最早出错的环节
==========================================================
看到错误答案时，先用事实区分症状、直接原因和根本原因，不靠猜测。
本文件把一次问答的管线事实记成 Trace，再由 diagnose 按顺序报告"最先失败的环节"。

管线：来源 → 切分 → 召回 → 重排 → 上下文 → 生成 → 引用

前置：2.4
运行：python tools/run_chapter.py 3.1（离线）
输出：三个示例（通过、上下文丢失、答案错误）各自的诊断结论
对应测试：python -m pytest chapters/test_new_lessons.py -q
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Trace:
    """一条简化的、人工标注的诊断记录。

    默认值表示"这一环节正常"，构造时只需改动出问题的字段。
    answer_correct 是评测标签，不是程序自动理解答案得到的结论。
    """

    case_id: str
    source_available: bool = True                      # 原始资料是否可用
    chunk_contains_fact: bool = True                   # 切分后事实是否完整保留
    expected_ids: tuple[str, ...] = ("refund-1",)      # 人工标注：应该用到的片段
    retrieved_ids: tuple[str, ...] = ("refund-1",)     # 召回了哪些片段
    ranked_ids: tuple[str, ...] = ("refund-1",)        # 重排、截断之后剩哪些
    context_ids: tuple[str, ...] = ("refund-1",)       # 最终进入上下文的片段
    cited_ids: tuple[str, ...] = ("refund-1",)         # 答案引用了哪些片段
    answer_correct: bool = True
    should_refuse: bool = False                        # 该样本是否应拒答（资料外问题）
    refused: bool = False                              # 系统实际是否拒答


def diagnose(trace: Trace) -> tuple[str, str]:
    """返回 (最先失败的环节, 下一步检查什么)。下游可能还有别的问题。"""
    # 1. 资料外问题：只看拒答和引用
    if trace.should_refuse:
        if not trace.refused:
            return "refusal", "检查范围、权限与拒答策略；先排查召回了无关资料"
        if trace.cited_ids:
            return "citation", "拒答时移除无关引用"
        return "pass", "资料外问题正确拒答"
    # 2. 资料内样本必须先有预期片段标签，否则无法判断检索对不对
    if not trace.expected_ids:
        return "labeling", "资料内样本必须标注预期片段，再诊断检索"
    # 3. 按管线顺序检查：源头的问题优先于下游
    if not trace.source_available:
        return "source", "检查数据版本、同步和访问权限"
    if not trace.chunk_contains_fact:
        return "chunking", "检查切分是否截断事实与限定条件"
    expected = set(trace.expected_ids)
    for name, ids, action in (
        ("retrieval", trace.retrieved_ids, "检查查询、召回模型与过滤条件"),
        ("reranking", trace.ranked_ids, "检查重排分数与截断阈值"),
        ("context", trace.context_ids, "检查去重、拼接与上下文预算"),
    ):
        if not expected <= set(ids):    # 期望片段在这一步之后已经不全
            return name, action
    # 4. 证据齐全却拒答或答错：问题在生成
    if trace.refused or not trace.answer_correct:
        return "generation", "证据已进入上下文；检查提示、模型与答案标注"
    # 5. 答案对了，还要看引用：必须覆盖预期片段，且都来自实际上下文（不能编造）
    if not expected <= set(trace.cited_ids) <= set(trace.context_ids):
        return "citation", "引用必须覆盖预期片段且来自实际上下文"
    return "pass", "当前已记录环节通过；仍需检查延迟与成本"


if __name__ == "__main__":
    for trace in (
        Trace("ok"),                                # 全部正常
        Trace("lost", context_ids=()),              # 召回有、上下文没有：context 环节
        Trace("wrong-answer", answer_correct=False),  # 证据齐全但答错：generation 环节
    ):
        print(trace.case_id, "→", *diagnose(trace))
