"""Day74 组合入口：配置备用模型时，正式生成链使用受控 fallback。"""

from __future__ import annotations

import os
from time import monotonic

from .application import SupportApplication
from .assistant import CustomerSupportAssistant
from .cache import AnswerCache, CachedApplication
from .conversation import PersistentHistory
from .idempotency import IdempotencyStore
from .knowledge import build_retriever
from .observability import ObservedApplication, Recorder
from .orders import OrderRepository
from .privacy import PrivacyApplication
from .providers import FallbackChatModel, TransientChatModel
from .readiness import ensure_ready
from .security import SecuredApplication
from .settings import Settings
from .thread_store import SQLiteThreadStore
from .tickets import TicketStore
from .workflow import WorkflowAssistant


def build_embeddings(model_name: str):
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=model_name)


def _build_chat(provider: str, model: str, base_url: str, api_key: str):
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model, base_url=base_url, temperature=0)
    if provider == "deepseek":
        if not api_key:
            raise RuntimeError("使用 DeepSeek 时必须配置 API Key")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=0,
        )
    raise ValueError(f"暂不支持 LLM_PROVIDER={provider}")


def build_chat_model(settings: Settings):
    primary = TransientChatModel(
        _build_chat(
            settings.llm_provider,
            settings.llm_model,
            settings.llm_base_url,
            settings.llm_api_key,
        )
    )
    fallback_provider = os.getenv("FALLBACK_LLM_PROVIDER", "").strip().lower()
    if not fallback_provider:
        return primary
    fallback = _build_chat(
        fallback_provider,
        os.getenv("FALLBACK_LLM_MODEL", settings.llm_model),
        os.getenv("FALLBACK_LLM_BASE_URL", settings.llm_base_url),
        os.getenv("FALLBACK_LLM_API_KEY", ""),
    )
    return FallbackChatModel(primary, fallback)


def build_assistant(settings: Settings | None = None) -> CustomerSupportAssistant:
    settings = settings or Settings.from_env()
    retriever = build_retriever(
        settings.knowledge_path,
        build_embeddings(settings.embedding_model),
        k=settings.retrieval_k,
        threshold=settings.relevance_threshold,
    )
    return CustomerSupportAssistant(retriever, build_chat_model(settings))


def build_application(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    ensure_ready(settings)
    core = SupportApplication(
        WorkflowAssistant(build_assistant(settings)),
        PersistentHistory(SQLiteThreadStore(settings.thread_db_path)),
        OrderRepository([]),
        TicketStore(),
        IdempotencyStore(),
    )
    protected = PrivacyApplication(SecuredApplication(core))
    cached = CachedApplication(protected, AnswerCache(60, monotonic))
    return ObservedApplication(cached, Recorder())
