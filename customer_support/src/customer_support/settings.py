"""集中读取客服助手的运行配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 当前文件位于 <项目>/src/customer_support/settings.py，parents[2] 是项目根目录。
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 尝试加载项目根目录的 .env。文件不存在时不会报错，系统环境变量仍然有效。
# load_dotenv 默认不会覆盖操作系统中已经设置的同名变量。
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """程序启动后使用的一组不可变配置。

    ``frozen=True`` 表示实例创建后不能随意修改字段，避免运行过程中配置变化。
    """

    # 业务资料的位置。
    knowledge_path: Path
    # 把文本转换成向量的模型路径或 Hugging Face 模型名。
    embedding_model: str
    # 本地 Ollama 占用 GPU 时，embedding 默认放在 CPU，避免争抢显存。
    embedding_device: str
    # 聊天模型提供商；Day51 支持 deepseek 和 ollama。
    llm_provider: str
    llm_model: str
    llm_base_url: str
    # 密钥只从环境读取，不能写死在源码中。
    llm_api_key: str
    # 一次最多给 LLM 几个相关文档块。
    retrieval_k: int = 3
    # 低于该相关度的结果会被 retriever 丢弃。
    relevance_threshold: float = 0.55

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量创建 Settings。

        返回值不是字典，而是有明确字段和类型的 ``Settings``，这样其他模块不用
        到处调用 ``os.getenv``，也不会在不同文件中使用不同默认值。
        """

        # 默认优先使用本机 Ollama；需要时可通过 LLM_PROVIDER=deepseek 切换。
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        default_model = "deepseek-chat" if provider == "deepseek" else "qwen3.5:9b"
        default_base_url = (
            "https://api.deepseek.com" if provider == "deepseek" else "http://localhost:11434"
        )
        return cls(
            # 业务资料属于项目本身，因此路径相对于 PROJECT_ROOT 计算，不依赖运行目录。
            knowledge_path=PROJECT_ROOT / "data" / "knowledge" / "customer_faq.md",
            embedding_model=os.getenv("EMBED_MODEL_PATH", "BAAI/bge-small-zh-v1.5").strip(),
            embedding_device=os.getenv("EMBED_DEVICE", "cpu").strip().lower(),
            llm_provider=provider,
            # 模型与服务地址的默认值都跟随 provider，避免 Ollama 请求误发到云端。
            llm_model=os.getenv("LLM_MODEL", default_model).strip(),
            llm_base_url=os.getenv("LLM_BASE_URL", default_base_url).strip(),
            # 优先使用项目统一变量，同时兼容常见的 DeepSeek 专用变量名。
            llm_api_key=(os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")).strip(),
        )
