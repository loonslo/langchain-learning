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


# ---------- 3. 工程版 routing：离线定标 → 在线分类 → 抽样监控 ----------
# 上面 is_simple() 的关键词规则只是冷启动。生产里的完整闭环是：
#   A. 离线（一次性 token 成本）：便宜模型跑历史问题 + judge 打分 → 产出"简单/复杂"标注
#      "难度"的定义 = 便宜模型能不能答对（实测），不靠拍脑袋
#   B. 在线（每次请求）：embedding 质心分类器做路由，本地推理 0 token、毫秒级
#   C. 监控（抽样 1~5%）：线上用 judge 复核路由质量，发现漂移就回炉重标
# token 只花在 A（一次性）和 C（抽样）上，B 不花钱——这就是成本与准确率的平衡点。

import json
import random

import numpy as np

# ---- A. 离线定标：一次性跑，产出标注数据（存 JSON，后面 B 直接用）----
JUDGE_PROMPT = """你是评审员。判断下面的"回答"是否正确、完整地回答了"问题"。
只输出一个字：是 或 否。
问题：{q}
回答：{a}"""


def offline_label(questions: list[str], out_path: str = "routing_labels.json") -> list[tuple[str, bool]]:
    """离线一次性：便宜模型作答 → judge 判对错。judge 说"是"= 便宜模型够用 = 简单。
    几百条问题也就跑一次，这是投资不是持续消耗。"""
    labeled = []
    for q in questions:
        ans = llm_cheap.invoke(q).content
        verdict = llm_strong.invoke(JUDGE_PROMPT.format(q=q, a=ans)).content
        labeled.append((q, verdict.strip().startswith("是")))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(labeled, f, ensure_ascii=False, indent=2)
    return labeled


# 演示用种子标注（真实场景由 offline_label 从历史日志产出）
SEED_LABELED = [
    ("你好，在吗", True),
    ("谢谢你的帮助", True),
    ("现在几点了", True),
    ("LangChain 是谁开发的", True),
    ("RAG 是什么的缩写", True),
    ("帮我把这句话翻译成英文：今天天气不错", True),
    ("详细对比 RAG 和微调在成本、时效、数据安全上的取舍", False),
    ("设计一个支持多租户的企业知识库权限方案", False),
    ("我的向量检索召回率很低，帮我分析可能的原因并给出排查步骤", False),
    ("写一个带重试和熔断的 LLM 调用封装，要求可配置", False),
    ("解释 LangGraph 的 checkpoint 机制并说明如何实现人工审批", False),
    ("如何为 Agent 的工具调用轨迹设计自动化评估指标", False),
]


# ---- B. 在线路由：embedding 质心分类器（本地推理，0 token）----
class EmbeddingRouter:
    """把两类标注问题各求一个质心向量；线上问题算 embedding 后看离谁近。
    用的是本地 BGE 模型，不调 API——这就是"判定本身不花钱"的关键。"""

    def __init__(self, labeled: list[tuple[str, bool]]):
        from common import get_embeddings
        self.emb = get_embeddings()
        simple = [q for q, ok in labeled if ok]
        hard = [q for q, ok in labeled if not ok]
        self.c_simple = np.mean(self.emb.embed_documents(simple), axis=0)
        self.c_hard = np.mean(self.emb.embed_documents(hard), axis=0)

    @staticmethod
    def _cos(a, b) -> float:
        return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

    def is_simple(self, question: str) -> bool:
        v = np.array(self.emb.embed_query(question))
        return self._cos(v, self.c_simple) > self._cos(v, self.c_hard)


# ---- C. 生产入口：路由 + 抽样监控 ----
AUDIT_RATE = 0.05          # 抽 5% 请求用 judge 复核，成本可控
AUDIT_LOG: list[dict] = []  # 生产里落库/上报，配合 Day36 成本统计看漂移


def ask_production(question: str, router: EmbeddingRouter) -> str:
    simple = router.is_simple(question)
    model = llm_cheap if simple else llm_strong
    print(f"  [prod-routing] {'简单→便宜模型' if simple else '复杂→强模型'}：{question[:20]}")
    ans = model.invoke(question).content
    if simple and random.random() < AUDIT_RATE:  # 只审便宜模型的答案，强模型默认可信
        verdict = llm_strong.invoke(JUDGE_PROMPT.format(q=question, a=ans)).content
        AUDIT_LOG.append({"q": question, "pass": verdict.strip().startswith("是")})
        print("  [audit] 本条被抽检，judge 结果：", verdict.strip()[:5])
    return ans


if __name__ == "__main__":
    print("===== 缓存：同一问题问两次 =====")
    q = "用一句话解释 RAG"
    print("答1：", ask_with_cache(q)[:50])
    print("答2：", ask_with_cache(q)[:50])   # 第二次应命中缓存

    print("\n===== routing（规则版）：简单 vs 复杂 =====")
    print("答：", ask_with_routing("你好")[:50])
    print("答：", ask_with_routing("详细对比 RAG 和微调在成本与时效上的取舍")[:50])

    print("\n===== routing（工程版）：embedding 分类器路由决策（本地，0 token）=====")
    router = EmbeddingRouter(SEED_LABELED)   # 生产里 labeled 来自 offline_label()
    for q in ["帮我翻译：机器学习", "如何设计 RAG 系统的灰度发布和回滚方案"]:
        print(f"  {q[:22]} → {'便宜模型' if router.is_simple(q) else '强模型'}")
    # 完整链路（含抽检）：ask_production(q, router)，需要 API key
    print("答：", ask_production("LangChain 的 LCEL 是什么", router)[:50])


# ----------------------------------------------------------
# 小结：
# - 缓存：重复问题直接返回，省 token 也降延迟；键用问题 hash，值存答案。
# - model routing：简单走便宜模型、复杂走强模型，按需分流控成本。
# - 工程版闭环：离线 judge 定标（一次性）→ 在线 embedding 分类器（0 token）
#   → 抽样 judge 监控（1~5%）。"难度"= 便宜模型实测能否答对，可量化、可回归。
# - 算账决定取舍：省钱幅度 ≈ 简单问题占比 ×（1 - 便宜/强模型价差）。
#   两个数都从日志和离线评估里量出来，不靠感觉。
# - 配合 Day36 的 token/成本统计，就能"先量化成本，再针对性优化"。
#
# 面试亮点（护城河）：别人说"关键词规则路由"，你说"routing 阈值是评估驱动的：
# 离线 judge 建标注、分类器承载标准、线上抽检防漂移，可用 pytest 回归验证"。
#
# 动手练习：
# 1. 给缓存加"过期时间"，超过 N 秒的旧答案视为失效、重新调用。
# 2. 用 capstone 的 eval 问题集跑一次 offline_label()，看便宜模型真实通过率，
#    再算一算 routing 能省多少钱。
# ----------------------------------------------------------
