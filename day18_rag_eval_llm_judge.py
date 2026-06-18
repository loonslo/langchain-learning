"""
Day 18 · 用大模型当裁判：评"答案正确性"和"忠实度"
==========================================================
测试工程师转 AI 应用开发  ★护城河★

Day14 的关键词匹配太死板：答案说"检索增强生成"、标准答案写"检索+生成"，
意思一样却被判没命中。更接近人判断的做法是 LLM-as-judge——
让"另一次 LLM 调用"给答案打分。这节评两个更难量化的指标：

1. 答案正确性：和标准答案比，对不对（不纠结用词，看意思）
2. 忠实度 (faithfulness)：答案是不是只根据给定上下文，有没有自己编（防幻觉关键）

知识点：LLM-as-judge 的 prompt 设计、用结构化输出拿到分数、它的坑
==========================================================
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from day11_rag_pdf_sources import build_retriever, build_rag_chain

load_dotenv()

# 裁判模型。建议 temperature=0，让打分稳定、可复现。
judge_llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0,
).with_structured_output(
    # 让裁判输出结构化分数，方便统计
    type("Verdict", (BaseModel,), {
        "__annotations__": {"score": int, "reason": str},
        "score": Field(description="1-5 分，5 为完全正确/完全忠实"),
        "reason": Field(description="打分理由，一句话"),
    }),
    method="function_calling",
)

# 评测集：要有标准答案（给"正确性"裁判做参照）
EVAL_SET = [
    {"question": "RAG 是什么", "reference": "RAG 是检索增强生成，先检索相关内容再生成回答"},
    {"question": "FAISS 有什么作用", "reference": "FAISS 用来存向量并做相似度检索"},
]


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
    retriever = build_retriever("test_doc.txt")
    rag_chain = build_rag_chain(retriever)

    total = 0
    for case in EVAL_SET:
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

    print(f"\n平均正确性：{total/len(EVAL_SET):.1f}/5")


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
