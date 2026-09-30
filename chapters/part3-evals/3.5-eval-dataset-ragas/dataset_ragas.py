"""
章节 3.5 · 造评测集（下）与 RAGAS 评估
==========================================================
本章完成评测集，并第一次接入业界通用的评测库：
1. 补齐评测集：加入拒答题（文档里没有，模型应说"不知道"）和引用准确性题，与 3.4 的事实题、
   跨段落题合并成 25 条，覆盖 4 类题型（可继续扩到 30–50 条）。拒答题直接量化"防幻觉防得住吗"。
2. 接入 RAGAS：不再手写指标，用现成的库计算 faithfulness（忠实度）、
   answer_relevancy（答案相关性）、context_precision（上下文精度）。

合并产物 eval_set_full.json 是整条评测线的单一数据源：
3.2（手写指标）、3.3（LLM 裁判）、3.6（LangSmith）、3.7（回归对比）都读它，不再各写一套。

知识点：
1. 拒答题怎么造、为什么重要
2. RAGAS 的数据格式：question / answer / contexts / ground_truth
3. 给 RAGAS 配国产模型（DeepSeek + 本地 embedding），不需要 OpenAI key（统一走 common）

前置：3.4（先运行它，生成 eval_set.json）
      RAGAS 评估部分另需：pip install ragas datasets、DEEPSEEK_API_KEY、本地 embedding 模型
运行：python tools/run_chapter.py 3.5
输出：chapters/shared-data/eval_set_full.json（25 条）；未安装 ragas 时只做合并，不做评估
==========================================================
"""

import json

from common import SHARED_DATA_DIR

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
    """合并 3.4 的基础集 + 本章补充集，写出 eval_set_full.json（评测线的单一数据源）。"""
    base = SHARED_DATA_DIR / "eval_set.json"
    if not base.exists():
        raise FileNotFoundError("先运行 3.4（dataset_build.py）生成 eval_set.json")
    base_cases = json.loads(base.read_text(encoding="utf-8"))
    full = base_cases + EXTRA
    (SHARED_DATA_DIR / "eval_set_full.json").write_text(
        json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
    return full


# ---------- 2. 跑 RAG 拿到 answer + contexts，喂给 RAGAS ----------
def run_ragas(dataset: list[dict]):
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from common import SAMPLE_DOC, get_llm, get_embeddings
    from pdf_sources import build_retriever, build_rag_chain

    retriever = build_retriever(SAMPLE_DOC)
    rag_chain = build_rag_chain(retriever)   # temperature=0，结果可复现

    # RAGAS 默认用 OpenAI；这里换成 DeepSeek + 本地 embedding，免 OpenAI key（统一走 common）
    judge_llm = LangchainLLMWrapper(get_llm(temperature=0))
    judge_emb = LangchainEmbeddingsWrapper(get_embeddings())

    # RAGAS 评的是"已经答完"的结果，所以先把每条问题跑一遍 RAG，收集四要素
    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    for case in dataset:
        if case["type"] == "refuse":
            continue  # 拒答题不进 RAGAS（它评相关性/忠实度，拒答另用 3.2 的拒答正确率）
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
    print(f"  已写出 {SHARED_DATA_DIR / 'eval_set_full.json'}（3.2、3.3、3.6、3.7 都读它）")
    print(f"  其中拒答题 {n['refuse']} 条（防幻觉底线）\n")

    try:
        print("===== RAGAS 离线评估（跳过拒答题）=====")
        print(run_ragas(full))
    except ModuleNotFoundError:
        print("(未装 RAGAS，跑 `pip install ragas datasets` 后再试)")

# ----------------------------------------------------------
# 小结：
# - 拒答题专测"防幻觉"：文档没有就该说不知道，硬答就是幻觉。这类题用 3.2 的
#   "拒答正确率"指标算，不进 RAGAS（RAGAS 评的是有答案时的质量）。
# - RAGAS 三个常用指标：
#     faithfulness     答案有没有忠于检索到的上下文（防编造）
#     answer_relevancy 答案有没有答到点上（别答非所问）
#     context_precision 检索到的上下文有多少是真有用的（衡量检索质量）
# - 给 RAGAS 配国产模型：用 LangchainLLMWrapper / LangchainEmbeddingsWrapper 包一层即可。
#
# 结果的表述方式（带数字、带方法、带改进）：
#   "25 条评测集，含 8 条拒答题；RAGAS 的 faithfulness 为 0.xx，拒答正确率 yy%；
#    调整切分策略后，忠实度提升到 0.zz"。
#
# 动手练习：故意把 chunk_size 设得很大重跑，看 context_precision 是不是掉了
#          （噪声多→精度降），用数字验证 2.7 的切分结论。
# ----------------------------------------------------------
