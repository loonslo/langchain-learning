"""
Day 78 · Context Engineering：给上下文做"预算管理"
==========================================================
测试工程师转 AI 应用开发  ← 1-33 补充包（把 Day17 重排 + Day35 压缩成体系）

喂给模型的上下文【不是越多越好】。三个硬约束：
- 窗口有限：塞不下所有召回的 chunk。
- 长上下文贵且慢：token 越多越烧钱、越慢。
- lost in the middle：放中间的信息容易被模型忽略，首尾更受重视。

所以"往 prompt 里放什么、放多少、怎么排"要当【预算管理】来做——这就是
Context Engineering（2026 高频 JD 词）。三板斧：

【一】裁剪（按 token 预算贪心装最相关的）：相关性排序后，在预算内能装几条装几条。
【二】排序（避免 lost-in-the-middle）：把最相关的放首尾，次要的塞中间。
【三】压缩（长内容摘要成短的）：Day35 的对话摘要、Day17 的 ContextualCompression 都属此类。

本文件纯本地可跑（不调 LLM，用简单 token 估算演示取舍逻辑）。

衔接：Day13 chunk、Day14 混合检索、Day17 reranker 决定"召回哪些"；
      本节决定召回之后"最终喂给模型哪些、怎么排"——是 RAG 的最后一公里。
==========================================================
"""


def est_tokens(text: str) -> int:
    """极简 token 估算（够教学用，不依赖 tiktoken）：
    中文字符 ≈ 1 token，其它（英文/数字/符号）≈ 0.3 token，向上取整。"""
    n = sum(1.0 if "一" <= c <= "鿿" else 0.3 for c in text)
    return int(n + 0.999)


# 一批"召回回来的候选片段"：score=相关性（越高越该留），text=内容
CANDIDATES = [
    {"id": "c1", "score": 0.95, "text": "RAG 用检索到的文档片段作为上下文，减少幻觉。"},
    {"id": "c2", "score": 0.90, "text": "混合检索 = 向量召回语义 + BM25 召回关键词，互补。"},
    {"id": "c3", "score": 0.60, "text": "reranker 用 cross-encoder 对召回结果重排取 top-k。"},
    {"id": "c4", "score": 0.40, "text": "向量数据库常见有 FAISS、Chroma、pgvector 等选型。"},
    {"id": "c5", "score": 0.20, "text": "这是一段和问题关系不大的背景噪声，价值最低。"},
]


# ============================================================
# 【一】裁剪：按 token 预算贪心装最相关的
# ============================================================
def pack_within_budget(cands: list, budget: int):
    """相关性从高到低排序，在 token 预算内能装就装，装不下的丢掉。"""
    ranked = sorted(cands, key=lambda c: c["score"], reverse=True)
    picked, used = [], 0
    for c in ranked:
        t = est_tokens(c["text"])
        if used + t <= budget:
            picked.append(c)
            used += t
        # 预算不够就跳过这条（它的相关性不足以挤占预算）
    return picked, used


def demo_budget():
    budget = 45
    picked, used = pack_within_budget(CANDIDATES, budget)
    print(f"  token 预算={budget}，各候选 tokens：",
          {c["id"]: est_tokens(c["text"]) for c in CANDIDATES})
    print(f"  装入（按相关性）：{[c['id'] for c in picked]}，共用 {used} tokens")
    dropped = [c["id"] for c in CANDIDATES if c not in picked]
    print(f"  丢弃（预算不够/相关性低）：{dropped} ← 低分噪声被挡在窗口外")


# ============================================================
# 【二】排序：把最相关的放首尾，避免 lost-in-the-middle
# ============================================================
def reorder_for_llm(picked: list) -> list:
    """最相关的放两端、次要的放中间——对抗'模型忽略中间内容'。"""
    ranked = sorted(picked, key=lambda c: c["score"], reverse=True)
    head, tail = [], []
    for i, c in enumerate(ranked):
        (head if i % 2 == 0 else tail).append(c)   # 交替分到前段/后段
    return head + tail[::-1]   # 后段反转拼回 → 高分落在首尾、低分居中


def demo_reorder():
    picked, _ = pack_within_budget(CANDIDATES, 60)
    ordered = reorder_for_llm(picked)
    print("  裁剪后按相关性：", [(c["id"], c["score"]) for c in
                                sorted(picked, key=lambda c: c['score'], reverse=True)])
    print("  重排后（喂给模型的顺序）：", [(c["id"], c["score"]) for c in ordered])
    print("  → 最高分落在首尾，最低分居中，减轻 lost-in-the-middle")


# ============================================================
# 【三】压缩：长内容摘要成短的（这里用规则模拟）
# ============================================================
def compress(text: str, max_tokens: int) -> str:
    """内容超预算就压缩。教学版用'掐头去尾'规则模拟；真实项目用 LLM 摘要（见 Day35）。"""
    if est_tokens(text) <= max_tokens:
        return text
    keep = max_tokens // 2
    return text[:keep] + "…（中间已压缩）…" + text[-keep:]


def demo_compress():
    long_text = "第一段讲背景。" * 6 + "关键结论在最后：混合检索显著提升召回。"
    print(f"  原文 {est_tokens(long_text)} tokens：{long_text}")
    out = compress(long_text, max_tokens=20)
    print(f"  压缩到 ~20 tokens：{out}")
    print("  → 真实项目用 LLM 摘要（Day35），关键是别把结论压没了")


if __name__ == "__main__":
    print("===== 【一】裁剪：token 预算内装最相关的 =====")
    demo_budget()
    print("\n===== 【二】排序：最相关放首尾，避免 lost-in-the-middle =====")
    demo_reorder()
    print("\n===== 【三】压缩：长内容摘要成短的 =====")
    demo_compress()


# ----------------------------------------------------------
# 小结：
# - Context Engineering = 把"喂给模型的上下文"当预算管理：放什么、放多少、怎么排。
# - 裁剪：按相关性 + token 预算贪心装，低分噪声挡在窗口外（省钱、提信噪比）。
# - 排序：最相关放首尾，对抗 lost-in-the-middle（中间内容易被忽略）。
# - 压缩：长内容摘要成短的（Day35 对话摘要 / Day17 ContextualCompression 都属此类）。
# - 一句话：用最少 token 喂最相关的信息，还要放对位置。
#
# 面试话术：
#   "上下文不是越多越好——窗口有限、长上下文贵、还有 lost-in-the-middle。我把它当
#    预算管理：按相关性给 chunk 打分，在 token 预算内贪心装最相关的，把最重要的放
#    首尾，长历史用摘要压缩。目标是最少 token 喂最相关的信息、放对位置。"
#
# 动手练习：把 est_tokens 换成真实 tiktoken 计数，接到你的 RAG 里——召回 top-20 后，
#          用本节三板斧裁到 token 预算内，跑 Day18 评测看质量有没有掉、token 省了多少。
# ----------------------------------------------------------
