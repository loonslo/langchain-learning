"""
Day 20 · 造评测集（下）+ RAGAS 离线评估
==========================================================
测试工程师转 AI 应用开发  ★护城河★

两件事收尾评测集，并第一次接业界标准工具：
1. 补齐评测集：加【拒答题】（文档里根本没有的，模型该老实说"不知道"）和
   【引用准确性】题，和 Day19 的事实+跨段落合并，凑到 25 条、覆盖 4 类题型（可继续扩到 30-50）。
   拒答题是测试背景的杀手锏——它直接量化"幻觉防得住吗"。
2. 接 RAGAS：不再手写指标，用业界通用库自动跑出 faithfulness(忠实度)、
   answer_relevancy(答案相关性)、context_precision(上下文精度) 等分数。

合并产物 eval_set_full.json 是整条评测线的"单一数据源"：
day17（手写指标）、day18（LLM 裁判）、day22（报告）都读它，不再各写一套。

知识点：
1. 拒答题怎么造、为什么重要
2. RAGAS 的数据格式：question / answer / contexts / ground_truth
3. 给 RAGAS 配国产模型（DeepSeek + 本地 embedding），免 OpenAI key（统一走 common）

依赖：pip install ragas datasets
==========================================================
"""

import json
from pathlib import Path

# ---------- 1. 补充样本：拒答 + 引用准确性 ----------
# should_refuse=True：文档里没有，正确行为是拒答；模型若硬答就是幻觉。
# 拒答 / 引用题不靠关键词命中判分，keywords 留空 []。
EXTRA = [
    # —— 拒答题（test_doc.txt 里完全没有的内容）——
    {"id": "r01", "question": "LangChain 是哪一年发布的？", "reference": "文档未提及，应拒答",
     "keywords": [], "expect_source": None, "type": "refuse", "should_refuse": True},
    {"id": "r02", "question": "FAISS 是哪家公司开发的？", "reference": "文档未提及，应拒答",
     "keywords": [], "expect_source": None, "type": "refuse", "should_refuse": True},
    {"id": "r03", "question": "LangGraph 支持 Java 吗？", "reference": "文档未提及，应拒答",
     "keywords": [], "expect_source": None, "type": "refuse", "should_refuse": True},
    {"id": "r04", "question": "Pinecone 的定价是多少？", "reference": "文档未提及，应拒答",
     "keywords": [], "expect_source": None, "type": "refuse", "should_refuse": True},
    {"id": "r05", "question": "RAG 和微调哪个准确率更高？", "reference": "文档未提及，应拒答",
     "keywords": [], "expect_source": None, "type": "refuse", "should_refuse": True},
    {"id": "r06", "question": "这份文档的作者是谁？", "reference": "文档未提及，应拒答",
     "keywords": [], "expect_source": None, "type": "refuse", "should_refuse": True},
    {"id": "r07", "question": "Chroma 最大能存多少条向量？", "reference": "文档未提及，应拒答",
     "keywords": [], "expect_source": None, "type": "refuse", "should_refuse": True},
    {"id": "r08", "question": "Agent 默认用什么大模型？", "reference": "文档未提及，应拒答",
     "keywords": [], "expect_source": None, "type": "refuse", "should_refuse": True},
    # —— 引用准确性（答对还不够，得标对来源/位置）——
    {"id": "c01", "question": "关于向量数据库的说明出自文档哪部分？",
     "reference": "出自讲向量数据库的段落（提到 FAISS、Chroma、Pinecone 那段）",
     "keywords": [], "expect_source": "test_doc.txt", "type": "citation", "should_refuse": False},
    {"id": "c02", "question": "请回答 LangGraph 的核心并说明依据来自哪里。",
     "reference": "核心是用图结构描述流程，依据来自讲 LangGraph 的段落",
     "keywords": [], "expect_source": "test_doc.txt", "type": "citation", "should_refuse": False},
]


def load_or_build_full_set() -> list[dict]:
    """合并 Day19 的基础集 + 本节补充集，写出 eval_set_full.json（评测线单一数据源）。"""
    base = Path("eval_set.json")
    if not base.exists():
        raise FileNotFoundError("先跑 day19_eval_dataset_build.py 生成 eval_set.json")
    day19 = json.loads(base.read_text(encoding="utf-8"))
    full = day19 + EXTRA
    Path("eval_set_full.json").write_text(
        json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
    return full


# ---------- 2. 跑 RAG 拿到 answer + contexts，喂给 RAGAS ----------
def run_ragas(dataset: list[dict]):
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from common import get_llm, get_embeddings
    from day11_rag_pdf_sources import build_retriever, build_rag_chain

    retriever = build_retriever("test_doc.txt")
    rag_chain = build_rag_chain(retriever)   # temperature=0，结果可复现

    # RAGAS 默认用 OpenAI；这里换成 DeepSeek + 本地 embedding，免 OpenAI key（统一走 common）
    judge_llm = LangchainLLMWrapper(get_llm(temperature=0))
    judge_emb = LangchainEmbeddingsWrapper(get_embeddings())

    # RAGAS 评的是"已经答完"的结果，所以先把每条问题跑一遍 RAG，收集四要素
    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    for case in dataset:
        if case["type"] == "refuse":
            continue  # 拒答题不进 RAGAS（它评相关性/忠实度，拒答另用 day17 的拒答率指标）
        q = case["question"]
        ctx = [d.page_content for d in retriever.invoke(q)]
        rows["question"].append(q)
        rows["answer"].append(rag_chain.invoke(q))
        rows["contexts"].append(ctx)
        rows["ground_truth"].append(case["reference"])

    result = evaluate(
        Dataset.from_dict(rows),
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=judge_llm, embeddings=judge_emb,
    )
    return result


if __name__ == "__main__":
    full = load_or_build_full_set()
    n = {t: sum(r["type"] == t for r in full) for t in ("fact", "multi_hop", "refuse", "citation")}
    print(f"评测集合并完成，共 {len(full)} 条：{n}")
    print(f"  已写出 eval_set_full.json（day17/18/22 都读它）")
    print(f"  其中拒答题 {n['refuse']} 条（防幻觉底线）\n")

    try:
        print("===== RAGAS 离线评估（跳过拒答题）=====")
        print(run_ragas(full))
    except ModuleNotFoundError:
        print("(未装 RAGAS，跑 `pip install ragas datasets` 后再试)")

# ----------------------------------------------------------
# 小结：
# - 拒答题专测"防幻觉"：文档没有就该说不知道，硬答=幻觉。这类题用 day17 的
#   "拒答正确率"指标算，不进 RAGAS（RAGAS 评的是有答案时的质量）。
# - RAGAS 三个常用指标：
#     faithfulness     答案有没有忠于检索到的上下文（防编造）
#     answer_relevancy 答案有没有答到点上（别答非所问）
#     context_precision 检索到的上下文有多少是真有用的（衡量检索质量）
# - 给 RAGAS 配国产模型：用 LangchainLLMWrapper / LangchainEmbeddingsWrapper 包一层即可。
#
# 验收话术（面试能讲）：
#   "我造了 25 条评测集，含 8 条拒答题；RAGAS 跑出 faithfulness 0.xx、
#    拒答正确率 yy%，改 chunk 策略后忠实度提升到 0.zz"——带数字、带方法、带改进。
#
# 动手练习：故意把 chunk_size 设得很大重跑，看 context_precision 是不是掉了
#          （噪声多→精度降），用数字验证 Day12 的切割结论。
# ----------------------------------------------------------
