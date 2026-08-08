"""Day59 组合入口：正式应用现在包含会话、图、订单、重试和工单。"""

from __future__ import annotations

from .application import SupportApplication
from .assistant import CustomerSupportAssistant
from .conversation import History
from .knowledge import build_retriever
from .orders import OrderRepository
from .settings import Settings
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


def build_application(settings: Settings | None = None) -> SupportApplication:
    return SupportApplication(
        WorkflowAssistant(build_assistant(settings)),
        History(max_turns=3),
        OrderRepository([]),
        TicketStore(),
    )
