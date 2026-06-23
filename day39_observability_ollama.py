"""
Day 39 · 可观测深化 + 本地推理框架（Ollama）了解
==========================================================
测试工程师转 AI 应用开发  ← 阶段4 工程化

两件事：
1. 可观测（深化 Day21）：上线后要能回答"哪条请求慢了/贵了/答错了"。
   除了 LangSmith trace，最朴素的是给每次调用记一条结构化日志：
   时间、问题、耗时、token、是否出错。有这些字段才能做监控和告警。
2. 本地推理框架 Ollama（只【了解】+ 跑一次）：把开源模型跑在自己机器上，
   数据不出门、没有 API 费。知道它怎么接即可，不深究推理加速原理。

依赖：Ollama 部分需本机装 Ollama 并 `ollama pull qwen2.5`（没装会自动跳过）。
==========================================================
"""

import time
import json
from datetime import datetime
from common import get_llm


# ---------- 1. 结构化调用日志：可观测的最小实现 ----------
def logged_invoke(question: str, logfile="calls.log.jsonl") -> str:
    """调用模型并记一条结构化日志（耗时/token/是否出错），追加到 jsonl。"""
    llm = get_llm(temperature=0)
    t0 = time.time()
    record = {"ts": datetime.now().isoformat(timespec="seconds"), "question": question}
    try:
        resp = llm.invoke(question)
        record["latency_ms"] = int((time.time() - t0) * 1000)
        record["tokens"] = (resp.usage_metadata or {}).get("total_tokens")
        record["ok"] = True
        answer = resp.content
    except Exception as e:
        record["latency_ms"] = int((time.time() - t0) * 1000)
        record["ok"] = False
        record["error"] = str(e)
        answer = ""
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print("  [log]", record)
    return answer


# ---------- 2. Ollama：本地跑开源模型（了解级，能接通即可）----------
def try_ollama():
    """如果本机装了 Ollama，就用本地模型答一句；没装则跳过。"""
    try:
        from langchain_ollama import ChatOllama
        local = ChatOllama(model="qwen2.5", temperature=0)
        print("  Ollama 本地模型回答：", local.invoke("一句话说说什么是向量").content[:50])
    except Exception as e:
        print(f"  (没装 Ollama / langchain-ollama，跳过本地模型) {type(e).__name__}")


if __name__ == "__main__":
    print("===== 1) 结构化调用日志 =====")
    logged_invoke("用一句话解释 RAG")
    print("  → 日志已追加到 calls.log.jsonl，可拿它统计 P95 延迟、错误率、token 趋势")

    print("\n===== 2) Ollama 本地推理（了解）=====")
    try_ollama()


# ----------------------------------------------------------
# 小结：
# - 可观测三件套：trace（看单条调用每一步，Day21）+ 结构化日志（统计延迟/错误/成本）
#   + 指标告警（基于日志算 P95、错误率，超阈值报警）。
# - Ollama：本地跑开源模型，数据不出门、零 API 费；接法和云模型几乎一样（换个 ChatXxx）。
#   只需【了解】：知道 vLLM / TGI / SGLang 是"自托管时提升吞吐的推理框架"，用到再深入。
#
# 动手练习：写个小脚本读 calls.log.jsonl，算平均/最大延迟和错误率——这就是最简监控。
# ----------------------------------------------------------
