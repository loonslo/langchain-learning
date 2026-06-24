"""
Day 43 · 成本优化：缓存 + model routing
==========================================================
测试工程师转 AI 应用开发  ← 阶段4 工程化

LLM 调用按 token 收费，规模一上来成本很可观。两招最常用：
1. 缓存：同一个问题问过就别再调模型，直接返回上次结果（省钱又快）
2. model routing：简单问题用便宜小模型，复杂问题才用贵的大模型
   （按需分流，把钱花在刀刃上）

本节用最朴素的实现把原理讲透；生产里缓存可换 Redis、routing 可上分类模型。
==========================================================
"""

import hashlib
from common import get_llm

llm_cheap = get_llm(temperature=0, model="deepseek-chat")   # 便宜模型（演示用同一个充当）
llm_strong = get_llm(temperature=0, model="deepseek-chat")  # 贵/强模型（换成你的大模型名）

# ---------- 1. 缓存：问题 → 答案。简单用 dict，键用问题的 hash ----------
_CACHE: dict[str, str] = {}


def _key(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def ask_with_cache(question: str) -> str:
    k = _key(question)
    if k in _CACHE:
        print("  [cache] 命中，直接返回（没调模型）")
        return _CACHE[k]
    print("  [cache] 未命中，调用模型")
    ans = llm_strong.invoke(question).content
    _CACHE[k] = ans
    return ans


# ---------- 2. model routing：按问题难度选模型 ----------
def is_simple(question: str) -> bool:
    """粗略判断：短、且像闲聊/问候的，算简单。生产可换成一个小分类模型。"""
    q = question.strip()
    simple_hint = any(w in q for w in ["你好", "谢谢", "再见", "几点", "是谁"])
    return len(q) <= 12 or simple_hint


def ask_with_routing(question: str) -> str:
    if is_simple(question):
        print("  [routing] 简单问题 → 便宜模型")
        return llm_cheap.invoke(question).content
    print("  [routing] 复杂问题 → 强模型")
    return llm_strong.invoke(question).content


if __name__ == "__main__":
    print("===== 缓存：同一问题问两次 =====")
    q = "用一句话解释 RAG"
    print("答1：", ask_with_cache(q)[:50])
    print("答2：", ask_with_cache(q)[:50])   # 第二次应命中缓存

    print("\n===== routing：简单 vs 复杂 =====")
    print("答：", ask_with_routing("你好")[:50])
    print("答：", ask_with_routing("详细对比 RAG 和微调在成本与时效上的取舍")[:50])


# ----------------------------------------------------------
# 小结：
# - 缓存：重复问题直接返回，省 token 也降延迟；键用问题 hash，值存答案。
# - model routing：简单走便宜模型、复杂走强模型，按需分流控成本。
# - 配合 Day36 的 token/成本统计，就能"先量化成本，再针对性优化"。
#
# 进阶（了解）：语义缓存（问法不同但意思相同也命中）、Redis 做分布式缓存、
#              用小模型做 routing 分类器。用到再上。
#
# 动手练习：给缓存加"过期时间"，超过 N 秒的旧答案视为失效、重新调用。
# ----------------------------------------------------------
