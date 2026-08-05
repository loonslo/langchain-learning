"""创建真实依赖，并把它们组合成可运行的客服助手。"""

from __future__ import annotations

from .assistant import CustomerSupportAssistant
from .knowledge import build_retriever
from .settings import Settings


def build_embeddings(model_name: str, device: str):
    """创建文本向量模型；只负责把文本转换成向量，不生成答案。"""
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": device},
    )


def build_chat_model(settings: Settings):
    """按配置创建聊天模型，并把不同 provider 收敛到 invoke 接口。"""

    if settings.llm_provider == "ollama":
        from .ollama_model import OllamaChatModel

        # 本地适配器不会向 qwen3.5 发送空 tools 数组，规避 Ollama 的 502。
        return OllamaChatModel(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            temperature=0,
        )

    if settings.llm_provider == "deepseek":
        # 在发送网络请求前检查密钥，给出比底层 401 更直接的错误信息。
        if not settings.llm_api_key:
            raise RuntimeError("使用 DeepSeek 时必须配置 LLM_API_KEY")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            temperature=0,
        )

    raise ValueError(f"不支持的 LLM_PROVIDER：{settings.llm_provider}；请选择 ollama 或 deepseek")


def build_assistant(settings: Settings | None = None) -> CustomerSupportAssistant:
    """按“配置 → embedding → retriever → LLM → assistant”顺序组装应用。"""
    # 调用方可以传入 Settings；普通 CLI 不传时才从环境创建。
    settings = settings or Settings.from_env()

    # embedding 用于检索，chat model 用于生成。它们是两个不同模型。
    embeddings = build_embeddings(settings.embedding_model, settings.embedding_device)
    retriever = build_retriever(
        settings.knowledge_path,
        embeddings,
        k=settings.retrieval_k,
        threshold=settings.relevance_threshold,
    )

    chat_model = build_chat_model(settings)
    return CustomerSupportAssistant(retriever, chat_model)
