"""
章节 3.3 · 用大模型当裁判：评"答案正确性"和"忠实度"
==========================================================
3.2 的关键词匹配太死板：答案写"检索增强生成"，标准答案写"检索+生成"，意思一样却判为没命中。
更接近人的判断的做法是 LLM-as-judge：让另一次 LLM 调用给答案打分。本章评两个更难量化的指标：
1. 答案正确性：和标准答案比，对不对（看意思，不纠结用词）
2. 忠实度（faithfulness）：答案是否只根据给定上下文，有没有编造（防幻觉的关键）

知识点：裁判 prompt 的设计、用结构化输出拿到分数、LLM 裁判的局限

评测集读 3.4、3.5 生成的 chapters/shared-data/eval_set_full.json（只评有标准答案、非拒答的题）；
没有时退回内置的 2 条示范集。

前置：1.3（结构化输出）、2.6；DEEPSEEK_API_KEY；本地 embedding 模型
运行：python tools/run_chapter.py 3.3（调用真实模型；每题调用 3 次：回答、正确性裁判、忠实度裁判）
输出：每题的正确性、忠实度分数和理由，以及平均正确性
==========================================================
"""

import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from common import SAMPLE_DOC, SHARED_DATA_DIR, get_llm
from pdf_sources import build_retriever, build_rag_chain


class Verdict(BaseModel):
    """裁判的结构化输出：分数 + 理由，方便统计也可追溯。"""
    score: int = Field(description="1-5 分，5 为完全正确/完全忠实")
    reason: str = Field(description="打分理由，一句话")


# 裁判模型。temperature=0 让打分稳定、可复现。
judge_llm = get_llm(temperature=0).with_structured_output(Verdict, method="function_calling")

# 兜底示范集（3.4、3.5 没运行时用）
INLINE_DEMO = [
    {"question": "RAG 是什么", "reference": "RAG 是检索增强生成，先检索相关内容再生成回答"},
    {"question": "FAISS 有什么作用", "reference": "FAISS 用来存向量并做相似度检索"},
]


def load_eval_set():
    """读全集/基础集里"非拒答且有标准答案"的题（裁判需要 reference 做参照）。"""
    for name in ("eval_set_full.json", "eval_set.json"):
        p = SHARED_DATA_DIR / name
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            return [r for r in data if not r.get("should_refuse") and r.get("reference")]
    return INLINE_DEMO


def judge_correctness(question, answer, reference):
    """答案正确性：对比标准答案，看意思对不对。"""
    prompt = ChatPromptTemplate.from_template("""
你是评测裁判。判断【模型答案】和【标准答案】意思是否一致，按 1-5 打分（只看意思，不纠结措辞）。
问题：{q}
标准答案：{ref}
模型答案：{ans}
""")
    return judge_llm.invoke(prompt.format(q=question, ref=reference, ans=answer))


def judge_faithfulness(question, answer, context):
    """忠实度：答案是不是只基于给定上下文，有没有编造（防幻觉）。"""
    prompt = ChatPromptTemplate.from_template("""
你是评测裁判。判断【模型答案】是否只依据【上下文】得出、没有编造上下文里没有的信息，按 1-5 打分。
上下文：{ctx}
问题：{q}
模型答案：{ans}
""")
    return judge_llm.invoke(prompt.format(ctx=context, q=question, ans=answer))


if __name__ == "__main__":
    eval_set = load_eval_set()
    print(f"裁判将评 {len(eval_set)} 条（非拒答、有标准答案）")
    retriever = build_retriever(SAMPLE_DOC)
    rag_chain = build_rag_chain(retriever)   # temperature=0

    total = 0
    for case in eval_set:
        q, ref = case["question"], case["reference"]
        answer = rag_chain.invoke(q)
        context = "\n".join(d.page_content for d in retriever.invoke(q))  # 这题召回的上下文

        correctness = judge_correctness(q, answer, ref)
        faithfulness = judge_faithfulness(q, answer, context)
        total += correctness.score

        print(f"\nQ: {q}")
        print(f"A: {answer[:80]}...")
        print(f"  正确性 {correctness.score}/5 —— {correctness.reason}")
        print(f"  忠实度 {faithfulness.score}/5 —— {faithfulness.reason}")

    print(f"\n平均正确性：{total/len(eval_set):.1f}/5")


# ----------------------------------------------------------
# 小结：
# - LLM-as-judge 比关键词匹配更接近人判断，能处理"同义不同词"
# - 用结构化输出（分数 + 理由）让结果可统计、可追溯
# - 裁判 temperature=0 提升打分稳定性
#
# 坑（务必知道）：
#   - 裁判自己也会犯错、有偏好（比如偏爱长答案），分数是参考不是真理
#   - 重要结论要抽样人工复核；裁判模型最好比被评模型更强
#
# 动手练习：故意构造一个"听起来对但其实编的"答案，看忠实度裁判能不能抓出来
# ----------------------------------------------------------
