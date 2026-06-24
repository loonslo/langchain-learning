"""
Day 26 · 评测报告 + 失败用例库
==========================================================
测试工程师转 AI 应用开发  ★护城河的产出物★

把 Day17-20 的评测结果汇总成一份报告，并把答错的 case 单独归档成"失败用例库"。
这是测试工程师的标志性产物——面试时你拿得出的不是"我觉得不错"，
而是"拒答正确率 X%、平均正确性 Y 分，这是失败的 3 条 case 和错因分析"。

知识点：
1. 把多条评测结果汇总成报告（总体指标 + 逐条明细），输出成 markdown
2. 失败用例库：归档答错的 case，标注错因（检索没召回 vs 召回了但生成错）
3. 工业级工具速览：RAGAS、LangSmith（什么时候值得上）
==========================================================
"""

import json
from datetime import datetime
from day11_rag_pdf_sources import build_retriever, build_rag_chain

EVAL_SET = [
    {"question": "RAG 是什么", "keywords": ["检索", "生成"], "should_refuse": False},
    {"question": "FAISS 有什么作用", "keywords": ["向量"], "should_refuse": False},
    {"question": "这篇文档讲了量子计算吗", "keywords": [], "should_refuse": True},
]
REFUSE_HINTS = ["没有提到", "我不知道", "未提及", "无法回答"]


def looks_like_refuse(answer):
    return any(h in answer for h in REFUSE_HINTS)


def run_eval(rag_chain, retriever):
    rows, failures = [], []
    for case in EVAL_SET:
        q = case["question"]
        answer = rag_chain.invoke(q)
        refused = looks_like_refuse(answer)

        if case["should_refuse"]:
            passed = refused
        else:
            passed = all(k in answer for k in case["keywords"])

        rows.append({"question": q, "answer": answer, "passed": passed})

        # 失败的 case 归档，并粗判错因：召回里有没有相关内容
        if not passed:
            hit_ctx = [d.page_content for d in retriever.invoke(q)]
            # 简单判断：召回内容里出现关键词 → 多半是"召回了但生成错"；否则"检索没召回"
            retrieved_ok = any(
                any(k in c for k in case["keywords"]) for c in hit_ctx
            ) if case["keywords"] else False
            cause = "召回了但生成错" if retrieved_ok else "检索没召回（或本应拒答却乱答）"
            failures.append({"question": q, "answer": answer, "cause": cause})

    return rows, failures


def write_report(rows, failures, path="eval_report.md"):
    passed = sum(r["passed"] for r in rows)
    lines = [
        f"# RAG 评测报告",
        f"\n生成时间：{datetime.now():%Y-%m-%d %H:%M}",
        f"\n## 总体",
        f"\n- 通过：{passed}/{len(rows)} = {passed/len(rows):.0%}",
        f"- 失败：{len(failures)} 条",
        f"\n## 逐条明细\n",
        "| 问题 | 通过 | 回答(截断) |",
        "|------|------|------------|",
    ]
    for r in rows:
        lines.append(f"| {r['question']} | {'✓' if r['passed'] else '✗'} | {r['answer'][:30]}... |")

    if failures:
        lines.append("\n## 失败用例分析\n")
        for f in failures:
            lines.append(f"- **{f['question']}** —— 错因：{f['cause']}")

    with open(path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    print(f"报告已写入 {path}")


if __name__ == "__main__":
    retriever = build_retriever("test_doc.txt")
    rag_chain = build_rag_chain(retriever)

    rows, failures = run_eval(rag_chain, retriever)
    write_report(rows, failures)

    # 失败用例库：单独存 json，方便回归时反复跑这些"老大难"
    with open("failures.json", "w", encoding="utf-8") as fp:
        json.dump(failures, fp, ensure_ascii=False, indent=2)
    print(f"失败用例库已存入 failures.json（{len(failures)} 条）")


# ----------------------------------------------------------
# 小结：
# - 评测报告 = 总体指标 + 逐条明细 + 失败分析，是能拿出手的成果物
# - 失败用例库把答错的 case 沉淀下来，每次改完 RAG 都重跑，做"回归测试"
# - 错因要分清：检索没召回（去调 chunk/检索）vs 召回了但生成错（去调 prompt）
#
# 工业级工具（了解，用到再上）：
#   - RAGAS：现成的 RAG 指标库（faithfulness、answer_relevancy 等）。
#            注意它默认调 OpenAI，要用 DeepSeek/本地模型得手动配 LLM 和 embedding。
#   - LangSmith：可视化每条 trace 的检索/生成步骤，定位"错在哪一步"很方便。
#
# 这套"评测集 + 指标 + 报告 + 失败库 + 回归"的闭环，正是测试背景转 AI 最硬的护城河。
# ----------------------------------------------------------
