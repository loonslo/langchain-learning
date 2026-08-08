"""Day68 组合入口：缓存位于安全/隐私之后，并且所有命中仍被观测。"""

from __future__ import annotations

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
from .security import SecuredApplication
from .settings import Settings
from .thread_store import SQLiteThreadStore
from .tickets import TicketStore
from .workflow import WorkflowAssistant


def build_embeddings(model_name: str):
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=model_name)


def build_chat_model(settings: Settings):
    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=settings.llm_model, base_url=settings.llm_base_url, temperature=0)
    if settings.llm_provider == "deepseek":
        if not settings.llm_api_key:
            raise RuntimeError("使用 DeepSeek 时必须配置 LLM_API_KEY")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            temperature=0,
        )
    raise ValueError(f"暂不支持 LLM_PROVIDER={settings.llm_provider}")


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
