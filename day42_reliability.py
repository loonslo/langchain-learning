"""
Day 42 · 可靠性：超时、重试、成本统计
==========================================================
测试工程师转 AI 应用开发

LLM 调用会超时、会被限流、会偶发失败。上线前必须加防护，还要能算清
"每次调用花了多少 token / 多少钱"。这节把这些工程基本功补上。

知识点：
1. 请求超时 timeout：别让一次卡住的调用拖垮整个服务
2. 指数退避重试：失败后等 1s、2s、4s 再试（先手写理解原理，再看生产做法）
3. token / 成本统计：用返回结果的 usage_metadata

本文件是教学材料，不是平行造一套"demo 版生产代码"：
- 手写重试：理解原理，仅此而已，不要在真实项目里用
- 生产版重试 + fallback：已经实现在 common.py 的 get_reliable_llm() 里，
  并且真的接进了 capstone/knowledge_base.py（chain()）和
  capstone/permissions.py（permission_chain()）——这两个是项目里
  用户会真实提问的链路。本文件只 import 它、演示怎么用。
- 缓存：只演示 + 说明适用边界，不接入生产问答链路（原因见下方注释）。
==========================================================
"""

import time
from langchain_core.messages import HumanMessage
from common import get_llm, get_reliable_llm

# 裸模型：无超时保护、无重试。评测/回归这类"结果要确定、失败就该报错"的
# 场景才用它（对照组，用来演示手写重试和暴露"不加防护会怎样"）。
llm = get_llm(temperature=0, timeout=20, max_retries=0)


# ========== 第 1 层：手写重试（只为理解原理，生产别用这个） ==========
def invoke_with_retry(messages, max_retries=3):
    """指数退避重试：第 1 次失败等 1s，第 2 次等 2s，第 3 次等 4s……

    为什么用指数退避：失败常因为限流/瞬时网络抖动，越往后等越久，
    给对方喘息空间，也避免你疯狂重试把自己也拖死。

    这版有两个生产不能接受的坑：
    ① 无差别重试——连"参数错误""鉴权失败"这种重试也没用的错误也照样等了重试
    ② 没有随机抖动 jitter——大量客户端同时失败、同时退避，会"同步重试风暴"再打爆一次服务
    往下看 get_reliable_llm 是怎么解决这两个问题的。
    """
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            wait = 2 ** attempt           # 1, 2, 4, ...
            print(f"第 {attempt + 1} 次失败：{e}；{wait}s 后重试")
            time.sleep(wait)
    raise RuntimeError(f"重试 {max_retries} 次仍失败")


# ========== 第 2 层：生产做法 ==========
# 真正上线用的实现在 common.py::get_reliable_llm()（全项目共用一处，改一处生效）：
#   - timeout：单次请求最多等 20s
#   - llm.with_retry(stop_after_attempt=4, wait_exponential_jitter=True)
#     LangChain 内置指数退避 + jitter，一行搞定，不用手写循环
#   - 可选 backup_model：主模型重试耗尽仍失败 → 自动切备用模型（with_fallbacks）
# capstone/knowledge_base.py 的 chain() 和 capstone/permissions.py 的
# permission_chain() 已经从 C.get_llm() 换成了 C.get_reliable_llm()。
reliable_llm = get_reliable_llm(temperature=0)


# ---- 进阶：如果 with_retry 的重试条件不够用（比如想区分"限流"和"5xx"
# 用不同等待策略、或者想在重试时打自己的日志/埋点），才需要上 tenacity 手写。
# 日常够用就别加这层复杂度——多一个依赖就多一处要维护的东西。
def build_tenacity_llm():
    from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
    try:
        from openai import APITimeoutError, RateLimitError, InternalServerError
        RETRYABLE = (APITimeoutError, RateLimitError, InternalServerError)
    except ImportError:
        RETRYABLE = (Exception,)   # 没装 openai SDK 就兜底，实际按你用的 SDK 异常类型填

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=20),
        retry=retry_if_exception_type(RETRYABLE),   # 只重试瞬时故障，参数错/鉴权错不重试
        reraise=True,                               # 重试耗尽后抛原始异常，别吞掉
    )
    def _invoke(messages):
        return llm.invoke(messages)
    return _invoke


# ---- 缓存：能省 token + 降延迟，但不是无脑接的东西 ----
# 原理：LangChain 的 SQLiteCache/InMemoryCache 是"精确匹配"缓存，key 是完整
# prompt 文本 + 模型参数。没有 TTL、没有淘汰策略，只增不减，文件会一直长大。
#
# 适用边界：
#   - 用：本地开发反复调试、evals/run_eval_platform.py 反复跑同一批固定 eval 题
#     （问题集合有限、可枚举，几百到几千条封顶，文件几十 MB 顶天）
#   - 不用：capstone/api.py 这类对外问答接口——用户问题几乎不重复，命中率低，
#     而且知识库文档更新（connector.py 增量同步）后，旧缓存答案不会失效，
#     等于让用户看到过时内容，这是正确性问题，不只是磁盘占用问题
#   - 真要在生产做缓存：换 RedisCache（可设 TTL）或语义缓存（相似度匹配、
#     不要求一字不差），并且要在文档更新时主动使旧缓存失效
def enable_eval_cache():
    """只在评测/开发脚本里调用，不要接入面向用户的问答链路。"""
    from langchain_core.globals import set_llm_cache
    from langchain_community.cache import SQLiteCache
    set_llm_cache(SQLiteCache(database_path=".llm_cache.db"))


if __name__ == "__main__":
    msgs = [HumanMessage("用一句话解释 RAG")]

    # 手写版（理解原理，能看到失败时的重试日志）
    resp = invoke_with_retry(msgs)
    print("手写重试版：", resp.content)

    # 生产版：直接用 common.get_reliable_llm()，capstone 里也是这么用的
    print("生产版（get_reliable_llm）：", reliable_llm.invoke(msgs).content)

    # 进阶：tenacity 精细控制（日常不需要，仅作了解）
    print("tenacity 版：", build_tenacity_llm()(msgs).content)

    # 缓存效果对比（仅评测/开发场景适用，见上方边界说明）
    enable_eval_cache()
    t0 = time.perf_counter(); llm.invoke(msgs); t1 = time.perf_counter()
    llm.invoke(msgs); t2 = time.perf_counter()
    print(f"缓存效果：首次 {t1 - t0:.2f}s，命中 {t2 - t1:.2f}s")

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
# - 手写版只为理解原理；生产用 common.get_reliable_llm()（with_retry + jitter）
# - 关键点：只重试瞬时故障，加 jitter 防同步风暴，reraise 别吞异常——
#   这些 LangChain 的 with_retry 已经处理好，不用自己再造一遍
# - get_reliable_llm 已经接进 capstone 的两条真实问答链路，不是孤立 demo
# - 缓存有明确适用边界：评测/开发用，别接生产对外问答（精确匹配命中率低 +
#   知识库更新后旧缓存不会失效，是正确性风险，不只是磁盘占用）
# - usage_metadata 让你能监控 token 和成本，是做成本告警/优化的数据来源
#
# 生产选型速记：
# - 就想加重试/主备切换 → common.get_reliable_llm()（本项目直接用这个）
# - 要精细控制"哪些错误重试" → tenacity（进阶，日常不需要）
# - 要省钱/提速的评测场景 → enable_eval_cache()
# - 还没做的进阶：model routing（简单问题路由到便宜模型）——属成本优化，用到再做
#
# 动手练习：把 get_reliable_llm() 接到 Day17 的 /chat 接口里，让服务更抗抖动
# ----------------------------------------------------------
