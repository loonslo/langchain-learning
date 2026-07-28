"""
公共配置与工厂（Day11+ 共用）
==========================================================
测试工程师转 AI 应用开发

把各 day 文件里重复的硬编码集中到这里：模型路径、LLM 初始化、中文分隔符。
换机器 / 换模型 / 换 key 只改这一处，不用动十几个文件。

为什么抽出来：
- 评测要可复现：LLM 默认 temperature=0 统一在工厂里设好，不靠每个文件各记一遍。
==========================================================
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

# ---- 模型路径：优先读环境变量，没配就用默认本地路径（换机器改 .env 即可）----
EMBED_MODEL_PATH = os.getenv(
    "EMBED_MODEL_PATH",
    r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-small-zh-v1___5",
)
RERANKER_MODEL_PATH = os.getenv(
    "RERANKER_MODEL_PATH",
    r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-reranker-base",
)

# 中文友好的递归切割分隔符：段落 > 换行 > 句号 > 逗号 > 空格 > 逐字兜底
ZH_SEPARATORS = ["\n\n", "\n", "。", "，", " ", ""]


@lru_cache(maxsize=1)
def get_embeddings():
    """本地 bge 中文 embedding。进程内只加载一次（lru_cache 缓存），避免重复 load。"""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL_PATH)


def get_llm(temperature: float = 0.0, model: str = "deepseek-chat", **kwargs):
    """DeepSeek 对话模型工厂（OpenAI 兼容）。
    评测 / 回归默认 temperature=0：同一输入每次输出一致、可复现。

    注意：这是"裸模型"，没有超时保护、没有重试。直接给用户答问题的链路
    （capstone 的 knowledge_base.py / permissions.py）应该用下面的
    get_reliable_llm，而不是直接用它。get_llm 留给评测/回归这类
    本来就要求"结果确定、失败就该让它失败"的场景。"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temperature,
        **kwargs,   # 透传 timeout / max_retries 等（day36 用）
    )


def get_reliable_llm(temperature: float = 0.0, model: str = "deepseek-chat",
                      backup_model: str | None = None, timeout: int = 20, **kwargs):
    """生产用 LLM 工厂：timeout + 指数退避重试（+ 可选主备 fallback）。

    这是 day42（可靠性）落地的地方——不是 demo，是全项目对外问答链路
    真正在用的入口。capstone/knowledge_base.py 的 chain()、
    capstone/permissions.py 的 permission_chain() 都调用它。

    - timeout：单次请求最多等 20s，不让一次卡住的调用拖垮整个请求
    - with_retry：LangChain 内置指数退避 + jitter，只需一行，不用手写
    - backup_model：可选，配置后主模型重试耗尽仍失败时自动切备用模型。
      目前项目只接了 DeepSeek 一家 provider，backup_model 若也是 DeepSeek
      家族模型，扛的是"某个模型限流/单模型故障"，扛不了"DeepSeek 整体挂了"；
      真正的跨 provider 高可用需要再接一个 api_key/base_url 不同的模型，
      本项目预算内暂不做，先把口子留好。
    """
    kwargs.setdefault("max_retries", 0)   # 关掉 SDK 内置重试，统一交给 with_retry 管理
    llm = get_llm(temperature=temperature, model=model, timeout=timeout, **kwargs).with_retry(
        stop_after_attempt=4,
        wait_exponential_jitter=True,
    )
    if backup_model:
        backup = get_llm(temperature=temperature, model=backup_model,
                          timeout=timeout, **kwargs).with_retry(stop_after_attempt=2)
        llm = llm.with_fallbacks([backup])
    return llm
