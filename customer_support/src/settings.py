"""读取多文档知识库、评测集和模型配置。

配置放在环境变量或 ``.env`` 文件中，而非写死在代码里。这样密钥不会进入 Git，
模型服务可切换 DeepSeek（云端）或 Ollama（本地，无需 API key）；embedding 仍
可在本地运行，不需要把文本向量请求发送到云端。
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
    knowledge_path: Path
    embedding_model: str
    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    embedding_device: str = "cpu"
    evaluation_path: Path = PROJECT_ROOT / "data" / "eval_cases.json"
    thread_db_path: Path = PROJECT_ROOT / "data" / "threads.db"
    retrieval_k: int = 3
    relevance_threshold: float = 0.55
    keyword_k: int = 3

    @classmethod
    def from_env(cls) -> "Settings":
        provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()
        if provider not in ("deepseek", "ollama"):
            raise ValueError(
                f"当前版本仅支持 deepseek / ollama，收到 LLM_PROVIDER={provider!r}；"
                "请将 LLM_PROVIDER 设置为 deepseek 或 ollama"
            )
        # Ollama 本地部署不需要真实密钥，仅需一个非空占位串满足底层接口约定。
        api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
        if provider == "ollama":
            api_key = api_key or "ollama-local"
            base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
            model = os.getenv("LLM_MODEL", "qwen3")
        else:
            base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
            model = os.getenv("LLM_MODEL", "deepseek-chat")
            if not api_key:
                raise RuntimeError("使用 DeepSeek 时必须配置 LLM_API_KEY")
        return cls(
            knowledge_path=PROJECT_ROOT / "data" / "knowledge",
            embedding_model=os.getenv("EMBED_MODEL_PATH", "BAAI/bge-small-zh-v1.5"),
            embedding_device=os.getenv("EMBED_DEVICE", "cpu").strip().lower(),
            llm_provider=provider,
            llm_model=model,
            llm_base_url=base_url,
            llm_api_key=api_key,
            evaluation_path=Path(
                os.getenv("EVAL_CASES_PATH", PROJECT_ROOT / "data" / "eval_cases.json")
            ),
            thread_db_path=Path(
                os.getenv("THREAD_DB_PATH", PROJECT_ROOT / "data" / "threads.db")
            ),
        )
