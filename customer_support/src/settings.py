"""读取多文档知识库、评测集和模型配置。

配置放在环境变量或 ``.env`` 文件中，而非写死在代码里。这样密钥不会进入 Git，
模型服务统一使用 DeepSeek；embedding 仍可在本地运行，不需要把文本向量请求发送到云端。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# ``settings.py`` 位于 ``项目根目录/src/``；向上一级就是项目根目录。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 读取项目根目录的 .env，并把其中尚未存在的变量放入当前进程环境。
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """应用运行所需的不可变配置集合。

每个字段都带有类型提示，例如 ``Path`` 表示文件路径、``str`` 表示文本，能帮助
编辑器和初学者发现传错值的问题。
    """
    knowledge_path: Path
    embedding_model: str
    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    embedding_device: str = "cpu"
    evaluation_path: Path = PROJECT_ROOT / "data" / "eval_cases.json"
    retrieval_k: int = 3
    relevance_threshold: float = 0.55
    keyword_k: int = 3

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量读取配置；当前版本只接受 DeepSeek 作为聊天模型服务。"""
        # ``strip`` 去掉意外空格，``lower`` 统一英文大小写；其他 provider 直接失败，
        # 避免配置残留时程序悄悄尝试连接本地 Ollama。
        provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()
        if provider != "deepseek":
            raise ValueError(
                f"当前版本仅支持 DeepSeek，收到 LLM_PROVIDER={provider!r}；"
                "请将 LLM_PROVIDER 设置为 deepseek"
            )
        default_model = "deepseek-chat"
        default_base_url = "https://api.deepseek.com"
        # ``cls(...)`` 表示创建当前类的实例；用它而非写死 Settings，子类也能复用该方法。
        return cls(
            knowledge_path=PROJECT_ROOT / "data" / "knowledge",
            # embedding 默认使用本机已下载的模型，避免每次运行都访问 Hugging Face Hub；
            # 它只负责知识库检索向量，不是聊天模型，也不改变 DeepSeek 的选择。
            embedding_model=os.getenv("EMBED_MODEL_PATH", "D:/models/bge-small-zh-v1.5"),
            embedding_device=os.getenv("EMBED_DEVICE", "cpu").strip().lower(),
            llm_provider=provider,
            llm_model=os.getenv("LLM_MODEL", default_model),
            llm_base_url=os.getenv("LLM_BASE_URL", default_base_url),
            llm_api_key=(os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")),
            evaluation_path=Path(
                os.getenv("EVAL_CASES_PATH", PROJECT_ROOT / "data" / "eval_cases.json")
            ),
        )
