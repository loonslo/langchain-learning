"""
Day 17 · RAG 评测入门：造评测集 + 手写三大指标
==========================================================
测试工程师转 AI 应用开发  ★这是你的护城河，重点★

"准确率提升了"——提升多少？靠什么算的？说不出来就是没评测。
测试工程师转 AI 最值钱的能力就在这：把"感觉还行"变成"带数字、带计算方法的结论"。

这节不依赖任何评测库，纯 Python 把三件事量化（最能理解指标本质，也一定跑得起来）：
1. 拒答正确率：文档里没有的问题，模型有没有老实说"不知道"（防幻觉的底线）
2. 关键词命中率：答案里有没有覆盖标准答案的关键信息
3. 检索命中率：应该被检索到的来源/内容，到底召回了没

评测集结构：每条 = 问题 + 期望（关键词 / 是否应拒答）。
为复用 Day10 封装好的 RAG，这里直接 import 它的函数——这就是"封装好便于测试"的价值。
==========================================================
"""

from day11_rag_pdf_sources import build_retriever, build_rag_chain

# ---------- 1. 评测集：问题 + 我们期望的结果 ----------
# 真实项目里这会是 30-50 条，覆盖：事实问答 / 跨段落 / 拒答 / 引用准确。
# 这里先用几条示范结构。should_refuse=True 表示"文档里没有，应该拒答"。
EVAL_SET = [
    {"question": "RAG 是什么", "keywords": ["检索", "生成"], "should_refuse": False},
    {"question": "FAISS 有什么作用", "keywords": ["向量"], "should_refuse": False},
    {"question": "这篇文档讲了量子计算吗", "keywords": [], "should_refuse": True},
    {"question": "文档里有 Python 装饰器的教程吗", "keywords": [], "should_refuse": True},
]

# 判断"模型是否拒答"的简单规则：回答里出现这些词就算拒答
REFUSE_HINTS = ["没有提到", "我不知道", "未提及", "无法回答"]


def looks_like_refuse(answer: str) -> bool:
    return any(h in answer for h in REFUSE_HINTS)


def evaluate(rag_chain):
    refuse_total = refuse_ok = 0      # 应拒答的题数 / 其中答对的
    answer_total = keyword_ok = 0     # 应回答的题数 / 其中命中关键词的

    for case in EVAL_SET:
        answer = rag_chain.invoke(case["question"])
        refused = looks_like_refuse(answer)
        print(f"\nQ: {case['question']}\nA: {answer[:80]}...")

        if case["should_refuse"]:
            refuse_total += 1
            ok = refused
            refuse_ok += ok
            print(f"   [应拒答] 实际{'拒答✓' if refused else '乱答✗'}")
        else:
            answer_total += 1
            hit = all(k in answer for k in case["keywords"])  # 关键词是否都覆盖
            keyword_ok += hit
            print(f"   [应回答] 关键词{case['keywords']} 命中：{'✓' if hit else '✗'}")

    # ---------- 算指标（带分母，可解释）----------
    print("\n" + "=" * 40)
    print("评测结果")
    if refuse_total:
        print(f"拒答正确率：{refuse_ok}/{refuse_total} = {refuse_ok/refuse_total:.0%}")
    if answer_total:
        print(f"关键词命中率：{keyword_ok}/{answer_total} = {keyword_ok/answer_total:.0%}")


if __name__ == "__main__":
    retriever = build_retriever("test_doc.txt")
    rag_chain = build_rag_chain(retriever)
    evaluate(rag_chain)


# ----------------------------------------------------------
# 小结：
# - 评测的核心是"造好带期望的评测集"，再用可解释的指标去算
# - 拒答正确率 = 防幻觉的底线；关键词命中 = 答得对不对的粗判
# - 这些指标都带分母，能说清"X/Y = Z%"，面试时这就是硬通货
#
# 局限：关键词完全匹配太死板（同义不同词会误判）。Day15 用 LLM-as-judge 解决。
#
# 动手练习：把评测集扩到 15 条以上，特意加几条"跨段落才能答"的难题
# ----------------------------------------------------------
