"""读取 Day52 起使用的多文档知识库和模型配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    knowledge_path: Path
    embedding_model: str
    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    retrieval_k: int = 3
    relevance_threshold: float = 0.55

    @classmethod
    def from_env(cls) -> "Settings":
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        default_model = "deepseek-chat" if provider == "deepseek" else "qwen3.5:9b"
        default_base_url = (
            "https://api.deepseek.com" if provider == "deepseek" else "http://localhost:11434"
        )
        return cls(
            knowledge_path=PROJECT_ROOT / "data" / "knowledge",
            embedding_model=os.getenv("EMBED_MODEL_PATH", "BAAI/bge-small-zh-v1.5"),
            llm_provider=provider,
            llm_model=os.getenv("LLM_MODEL", default_model),
            llm_base_url=os.getenv("LLM_BASE_URL", default_base_url),
            llm_api_key=(os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")),
        )
