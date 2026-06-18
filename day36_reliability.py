"""
Day 36 · 可靠性：超时、重试、成本统计
==========================================================
测试工程师转 AI 应用开发

LLM 调用会超时、会被限流、会偶发失败。上线前必须加防护，还要能算清
"每次调用花了多少 token / 多少钱"。这节把这些工程基本功补上。

知识点：
1. 请求超时 timeout：别让一次卡住的调用拖垮整个服务
2. 指数退避重试：失败后等 1s、2s、4s 再试（手写，理解原理）
3. token / 成本统计：用返回结果的 usage_metadata

重试这里手写以便理解；生产里也可用 tenacity 库（@retry 装饰器）。
==========================================================
"""

import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

# timeout：单次请求最多等多久（秒）。max_retries=0 关掉内置重试，下面手写演示。
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    timeout=20,
    max_retries=0,
)


def invoke_with_retry(messages, max_retries=3):
    """指数退避重试：第 1 次失败等 1s，第 2 次等 2s，第 3 次等 4s……

    为什么用指数退避：失败常因为限流/瞬时网络抖动，越往后等越久，
    给对方喘息空间，也避免你疯狂重试把自己也拖死。
    """
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            wait = 2 ** attempt           # 1, 2, 4, ...
            print(f"第 {attempt + 1} 次失败：{e}；{wait}s 后重试")
            time.sleep(wait)
    raise RuntimeError(f"重试 {max_retries} 次仍失败")


if __name__ == "__main__":
    resp = invoke_with_retry([HumanMessage("用一句话解释 RAG")])
    print("回答：", resp.content)

    # ---------- token / 成本统计 ----------
    # usage_metadata 里有 input_tokens / output_tokens / total_tokens
    usage = resp.usage_metadata
    print("\ntoken 用量：", usage)

    # 粗算成本：按你模型的实际单价填（这里用占位单价示范）
    PRICE_PER_1K = 0.001   # 元 / 1K token（换成你的真实价）
    if usage:
        cost = usage["total_tokens"] / 1000 * PRICE_PER_1K
        print(f"本次约花费：{cost:.5f} 元")


# ----------------------------------------------------------
# 小结：
# - timeout + 重试是 LLM 调用的标配，缺了线上一定出事
# - 指数退避对"限流/瞬时故障"友好，比固定间隔猛重试更稳
# - usage_metadata 让你能监控 token 和成本，是做成本告警/优化的数据来源
#
# 进阶（了解）：provider fallback（主模型挂了切备用模型）、缓存（重复问题不重复调）、
#              model routing（简单问题用便宜模型）——属于成本/可用性优化，用到再做
#
# 动手练习：把 invoke_with_retry 包到 Day17 的 /chat 接口里，让服务更抗抖动
# ----------------------------------------------------------
