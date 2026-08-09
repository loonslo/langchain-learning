"""创建真实依赖并把它们组合成可运行的客服助手。

这类文件常被称为 composition root（组合入口）。``assistant.py`` 保存稳定业务规则，
本文件处理“今天具体用哪个模型、怎样创建它”的运行细节。

可以把它看成装配车间：配置给出零件型号，函数依次创建向量模型、检索器和聊天模型，
最后交给 ``CustomerSupportAssistant`` 协调工作。
"""

from __future__ import annotations

from .application import SupportApplication
from .assistant import CustomerSupportAssistant
from .conversation import History
from .knowledge import build_retriever
from .settings import Settings
from .workflow import WorkflowAssistant


def build_embeddings(model_name: str, device: str):
    """创建文本向量模型；它只负责把文本转换成向量，不生成客服答案。

    向量可理解为“文本意思的数字坐标”。意思相近的文字，坐标通常也较接近，
    因而可用于从知识库中找资料。
    """
    # 延迟导入：只在真正启动产品时才加载较重的第三方库，纯业务测试可更轻量。
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=model_name, model_kwargs={"device": device})


def build_chat_model(settings: Settings):
    """按配置创建聊天模型，并把不同供应商统一为 ``invoke`` 接口。"""

    # provider（供应商）决定模型运行在本机还是通过网络调用。
    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        # Ollama 在本机运行，通常不需要 API Key（访问密钥）。
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
    raise ValueError(f"暂不支持 LLM_PROVIDER={settings.llm_provider}")


def build_assistant(settings: Settings | None = None) -> CustomerSupportAssistant:
    """按“配置 → embedding → retriever → LLM → assistant”顺序装配应用。

    这个顺序反映依赖关系：检索器先需要向量模型，助手再需要检索器和聊天模型。
    """

    # 调用方可以传入 Settings；主程序不传时才从环境创建。
    settings = settings or Settings.from_env()

    # embedding 用于检索，chat model 用于生成。它们是两个不同模型。
    retriever = build_retriever(
        settings.knowledge_path,
        build_embeddings(settings.embedding_model, settings.embedding_device),
        k=settings.retrieval_k,
        threshold=settings.relevance_threshold,
        keyword_k=settings.keyword_k,
    )
    return CustomerSupportAssistant(retriever, build_chat_model(settings))

def build_application(settings: Settings | None = None) -> SupportApplication:
    """正式主程序使用这个入口；离线评测仍可直接构建底层 assistant。"""
    assistant = WorkflowAssistant(build_assistant(settings))
    return SupportApplication(assistant, History(max_turns=3))
