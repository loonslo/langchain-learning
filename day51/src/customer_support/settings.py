"""读取项目运行配置。

这个模块只回答一个问题：“当前机器应该使用哪份资料、哪个 embedding 模型和
哪个聊天模型？”它不加载文档、不调用模型，也不执行业务问答。

把配置集中在这里的原因：源码可以提交到 Git；API Key 和机器上的模型路径不能
写死在源码中，它们应该来自没有提交的 ``.env`` 文件或系统环境变量。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 当前文件位于 <项目>/src/customer_support/settings.py。
# parents[0] 是 customer_support，parents[1] 是 src，parents[2] 才是项目根目录。
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 尝试加载项目根目录的 .env。文件不存在时不会报错，系统环境变量仍然有效。
# load_dotenv 默认不会覆盖操作系统中已经设置的同名变量。
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """程序启动后使用的一组不可变配置。

    ``frozen=True`` 表示实例创建后不能随意修改字段，避免程序运行到一半时配置
    突然变化。Day51 暂时把配置保持简单，后续再增加校验和多环境管理。
    """

    # 业务资料的位置。
    knowledge_path: Path
    # 把文本转换成向量的模型路径或 Hugging Face 模型名。
    embedding_model: str
    # 聊天模型提供商；Day51 支持 deepseek 和 ollama。
    llm_provider: str
    llm_model: str
    llm_base_url: str
    # 只从环境读取。仓库中的 .env.example 只能放占位符。
    llm_api_key: str
    # 一次最多交给 LLM 几个相关文档块。
    retrieval_k: int = 3
    # 低于该相关度的结果会被 retriever 丢弃。
    relevance_threshold: float = 0.55

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量创建 Settings。

        返回值不是字典，而是有明确字段和类型的 ``Settings``，这样其他模块不用
        到处调用 ``os.getenv``，也不会在不同文件中使用不同默认值。
        """

        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        default_model = "deepseek-chat" if provider == "deepseek" else "qwen3.5:9b"
        default_base_url = (
            "https://api.deepseek.com" if provider == "deepseek" else "http://localhost:11434"
        )
        return cls(
            # 业务资料属于项目本身，因此路径相对于 PROJECT_ROOT 计算，不依赖运行目录。
            knowledge_path=PROJECT_ROOT / "data" / "knowledge" / "customer_faq.md",
            embedding_model=os.getenv("EMBED_MODEL_PATH", "BAAI/bge-small-zh-v1.5"),
            llm_provider=provider,
            # 没有显式配置模型时，根据 provider 选择一个教学用默认值。
            llm_model=os.getenv("LLM_MODEL", default_model),
            llm_base_url=os.getenv("LLM_BASE_URL", default_base_url),
            llm_api_key=(os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")),
        )
