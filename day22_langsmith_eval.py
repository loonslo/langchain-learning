"""
Day 22 · LangSmith：trace 可视化 + 在线评估
==========================================================
测试工程师转 AI 应用开发  ★护城河：可观测★

前面 day17-20 的评测是"本地算指标"。但 RAG 答错时，你还想知道——
错在检索哪一步？召回了什么？prompt 收到的上下文长啥样？
LangSmith 把每次调用的"检索→拼上下文→生成"每一步都记成一条 trace，
出问题点开就能看，不用塞一堆 print。这就是"可观测"，面试高频词。

两件事：
1. 开 trace：设几个环境变量，之后所有 LangChain/LangGraph 调用自动上报，零改代码。
2. 在线评估：把评测集传成 LangSmith dataset，用评分函数批量跑，结果在网页看趋势。

前置：在 .env 里配 LANGSMITH_API_KEY（https://smith.langchain.com 注册免费拿）。
      没配也能跑——trace 部分会跳过，不报错。
==========================================================
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---- 开 trace：这几个环境变量一设，普通调用就自动产生 trace（不用改业务代码）----
HAS_KEY = bool(os.getenv("LANGSMITH_API_KEY"))
if HAS_KEY:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ.setdefault("LANGSMITH_PROJECT", "rag-day21")

import json
from pathlib import Path
from day11_rag_pdf_sources import build_retriever, build_rag_chain


def trace_demo():
    """正常跑一次 RAG。只要配了 key，这次调用的每一步都会出现在 LangSmith。"""
    retriever = build_retriever("test_doc.txt")
    chain = build_rag_chain(retriever)
    ans = chain.invoke("RAG 是什么")
    print("回答：", ans[:80], "...")
    if HAS_KEY:
        print("→ 打开 https://smith.langchain.com，进 rag-day21 项目看这次的 trace：")
        print("  能看到 retriever 召回了哪些块、prompt 实际收到的上下文、LLM 输入输出。")
    else:
        print("（未配 LANGSMITH_API_KEY，跳过 trace。配好后重跑即可在网页看每一步。）")


def langsmith_eval():
    """进阶：把评测集传成 dataset，定义评分函数，用 LangSmith 批量评估。
    依赖 eval_set_full.json（先跑 day19、day20 生成）。"""
    if not HAS_KEY:
        print("（未配 key，跳过在线评估）")
        return

    from langsmith import Client, evaluate

    data_file = Path("eval_set_full.json")
    if not data_file.exists():
        print("先跑 day19、day20 生成 eval_set_full.json 再来")
        return
    cases = [c for c in json.loads(data_file.read_text(encoding="utf-8"))
             if not c.get("should_refuse")]   # 在线评估先只跑有答案的题

    client = Client()
    ds_name = "rag-eval-day21"
    if not client.has_dataset(dataset_name=ds_name):
        ds = client.create_dataset(ds_name)
        client.create_examples(
            dataset_id=ds.id,
            inputs=[{"question": c["question"]} for c in cases],
            outputs=[{"reference": c["reference"]} for c in cases],
        )

    retriever = build_retriever("test_doc.txt")
    chain = build_rag_chain(retriever)

    # target：被评系统。LangSmith 会把 dataset 每条 input 喂进来
    def target(inputs: dict) -> dict:
        return {"answer": chain.invoke(inputs["question"])}

    # 评分函数（现代签名）：拿到模型输出 + 参考答案，返回打分
    def keyword_ok(outputs: dict, reference_outputs: dict) -> dict:
        ref = reference_outputs["reference"]
        ans = outputs["answer"]
        # 简化：参考答案里的关键短词是否出现在回答里（真实项目可换 LLM-judge）
        hit = any(w and w in ans for w in ref.replace("、", " ").split())
        return {"key": "keyword_hit", "score": int(hit)}

    results = evaluate(target, data=ds_name, evaluators=[keyword_ok],
                       experiment_prefix="rag-day21")
    print("在线评估已提交，去 LangSmith 看结果对比：", results)


if __name__ == "__main__":
    print("===== 1) trace 演示 =====")
    trace_demo()
    print("\n===== 2) LangSmith 在线评估（需 key + eval_set_full.json）=====")
    try:
        langsmith_eval()
    except Exception as e:
        print(f"(在线评估出错，多为 key/版本/网络问题，trace 部分不受影响) {e}")


# ----------------------------------------------------------
# 小结：
# - trace = 可观测：开几个环境变量，调用链每一步自动上报，排查"错在哪一步"不靠 print。
# - LangSmith evaluate = 在线评估：dataset + 评分函数批量跑，网页看实验对比和趋势。
# - 和 day17-20 的关系：本地指标轻量、随手跑；LangSmith 适合团队协作、留存历史、看趋势。
#
# 面试话术：
#   "我用 LangSmith trace 区分检索失败和生成幻觉——召回里没相关块就是检索问题，
#    召回对了但答跑偏就是生成问题，定位到具体步骤再改。"
# ----------------------------------------------------------
