"""创建真实依赖并把它们组合成可运行的客服助手。

这类文件常被称为 composition root（组合入口）。``assistant.py`` 保存稳定业务规则，
本文件处理“今天具体用哪个模型、怎样创建它”的运行细节。
"""

from __future__ import annotations

from .assistant import CustomerSupportAssistant
from .knowledge import build_retriever
from .settings import Settings


def build_embeddings(model_name: str):
    """创建文本向量模型；它只负责把文本转换成向量，不生成客服答案。"""

    # 延迟导入让纯业务单元测试不必初始化体积较大的模型依赖。
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=model_name)


def build_chat_model(settings: Settings):
    """按配置创建聊天模型，并把不同 provider 收敛到 invoke 接口。"""

    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        # Ollama 在本机运行，通常不需要 API Key。
        return ChatOllama(
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
    raise ValueError(f"Day51 暂不支持 LLM_PROVIDER={settings.llm_provider}")


def build_assistant(settings: Settings | None = None) -> CustomerSupportAssistant:
    """按“配置 → embedding → retriever → LLM → assistant”顺序组装应用。"""

    # 调用方可以传入 Settings；主程序不传时才从环境创建。
    settings = settings or Settings.from_env()

    # embedding 用于检索，chat model 用于生成。它们是两个不同模型。
    embeddings = build_embeddings(settings.embedding_model)
    retriever = build_retriever(
        settings.knowledge_path,
        embeddings,
        k=settings.retrieval_k,
        threshold=settings.relevance_threshold,
        keyword_k=settings.keyword_k,
    )
    chat_model = build_chat_model(settings)
    return CustomerSupportAssistant(retriever, chat_model)
