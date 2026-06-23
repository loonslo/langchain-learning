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
    评测 / 回归默认 temperature=0：同一输入每次输出一致、可复现。"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temperature,
        **kwargs,   # 透传 timeout / max_retries 等（day36 用）
    )
