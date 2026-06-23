"""
Day 17 · RAG 评测入门：造评测集 + 手写三大指标
==========================================================
测试工程师转 AI 应用开发  ★这是你的护城河，重点★

"准确率提升了"——提升多少？靠什么算的？说不出来就是没评测。
测试工程师转 AI 最值钱的能力就在这：把"感觉还行"变成"带数字、带计算方法的结论"。

这节不依赖任何评测库，纯 Python 把两件事量化（最能理解指标本质，也一定跑得起来）：
1. 拒答正确率：文档里没有的问题，模型有没有老实说"不知道"（防幻觉的底线）
2. 关键词命中率：答案里有没有覆盖标准答案的核心关键词

★重点改进：评测集不再写死在本文件，而是直接读 Day19/20 造的 eval_set_full.json。
  "造评测集"和"跑评测"用同一份数据——这才是真正的回归用例库，不是两套各写一遍。
  （还没跑过 day19/20 时，自动退回内置示范集，保证本文件能独立运行。）
==========================================================
"""

import json
from pathlib import Path
from day11_rag_pdf_sources import build_retriever, build_rag_chain

# 内置示范集（兜底）：当 day19/20 的 JSON 还没生成时用，保证本文件能独立跑
INLINE_DEMO = [
    {"question": "RAG 是什么", "keywords": ["检索", "生成"], "should_refuse": False},
    {"question": "FAISS 有什么作用", "keywords": ["向量"], "should_refuse": False},
    {"question": "这篇文档讲了量子计算吗", "keywords": [], "should_refuse": True},
    {"question": "文档里有 Python 装饰器的教程吗", "keywords": [], "should_refuse": True},
]

# 判断"模型是否拒答"的简单规则：回答里出现这些词就算拒答
# （比 Day11 prompt 里的"文档中没有提到"多覆盖几种常见说法，减少漏判）
REFUSE_HINTS = ["没有提到", "我不知道", "未提及", "无法回答", "未涉及", "找不到", "没有相关"]


def load_eval_set():
    """优先用 Day20 全集，其次 Day19 基础集，都没有才用内置示范。"""
    for name in ("eval_set_full.json", "eval_set.json"):
        p = Path(name)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8")), name
    return INLINE_DEMO, "内置示范集"


def looks_like_refuse(answer: str) -> bool:
    return any(h in answer for h in REFUSE_HINTS)


def evaluate(rag_chain, eval_set):
    refuse_total = refuse_ok = 0      # 应拒答的题数 / 其中答对的
    answer_total = keyword_ok = 0     # 有关键词的应答题数 / 其中命中的

    for case in eval_set:
        answer = rag_chain.invoke(case["question"])
        refused = looks_like_refuse(answer)
        print(f"\nQ: {case['question']}\nA: {answer[:80]}...")

        if case.get("should_refuse"):
            refuse_total += 1
            refuse_ok += refused
            print(f"   [应拒答] 实际{'拒答✓' if refused else '乱答✗'}")
        else:
            kws = case.get("keywords", [])
            if not kws:
                # 没给关键词的题（如引用题）跳过命中率，避免误判
                print("   [应回答] 无关键词，跳过命中率统计")
                continue
            answer_total += 1
            hit = all(k in answer for k in kws)   # 关键词是否都覆盖
            keyword_ok += hit
            print(f"   [应回答] 关键词{kws} 命中：{'✓' if hit else '✗'}")

    # ---------- 算指标（带分母，可解释）----------
    print("\n" + "=" * 40)
    print("评测结果")
    if refuse_total:
        print(f"拒答正确率：{refuse_ok}/{refuse_total} = {refuse_ok/refuse_total:.0%}")
    if answer_total:
        print(f"关键词命中率：{keyword_ok}/{answer_total} = {keyword_ok/answer_total:.0%}")


if __name__ == "__main__":
    eval_set, src = load_eval_set()
    print(f"评测集来源：{src}，共 {len(eval_set)} 条")
    retriever = build_retriever("test_doc.txt")
    rag_chain = build_rag_chain(retriever)   # temperature=0，结果可复现
    evaluate(rag_chain, eval_set)


# ----------------------------------------------------------
# 小结：
# - 评测的核心是"造好带期望的评测集"，再用可解释的指标去算
# - 拒答正确率 = 防幻觉的底线；关键词命中 = 答得对不对的粗判
# - 这些指标都带分母，能说清"X/Y = Z%"，面试时这就是硬通货
# - 评测集从 JSON 读，和 day19/20/22 共用一份，改一处全线生效
#
# 局限：关键词完全匹配太死板（同义不同词会误判）。Day18 用 LLM-as-judge 解决。
#
# 动手练习：先跑 day19、day20 生成 eval_set_full.json，再跑本文件，看 30+ 条的指标
# ----------------------------------------------------------
