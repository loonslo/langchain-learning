"""实现一次完整的客服知识问答业务用例。

本模块不知道 Chroma、DeepSeek 或 Ollama 如何初始化，只依赖两个最小能力：
Retriever 能按问题返回 Document，ChatModel 能按消息生成回答。这样业务规则既能
连接真实 LangChain 组件，也能在测试中换成不会联网的 Fake。

阅读主线：``ask(问题) → 检索证据 → 无证据拒答 / 有证据生成 → 附上真实来源``。
“检索”和“生成”是两件事：前者找资料，后者把资料改写成自然语言。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

# 拒答文案集中定义，正式代码和测试共享同一个业务约定，避免两处文字悄悄不一致。
REFUSAL = "知识库中没有足够信息，请转人工客服。"

# Prompt 只约束“拿到证据以后怎样回答”。是否有足够证据不能只靠这段文字，
# ask() 还会在调用模型前执行一次确定性的空证据检查。
PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是企业客服助手。只能根据给定证据回答；证据不足时必须回复："
            f"{REFUSAL} 不要使用模型记忆补充事实。",
        ),
        ("human", "<evidence>\n{context}\n</evidence>\n\n用户问题：{question}"),
    ]
)


class Retriever(Protocol):
    """描述 assistant 需要的检索能力，而不是绑定某个具体数据库。

    只要一个对象有同样的 ``invoke`` 方法，就可以作为 Retriever 使用；这样 Chroma
    与测试中的 FakeRetriever 都能接入。
    """

    def invoke(self, question: str) -> list[Document]: ...


class ChatModel(Protocol):
    """描述聊天模型的最小能力：接收消息，返回一个带回答内容的对象。"""

    def invoke(self, messages): ...


@dataclass(frozen=True)
class SupportAnswer:
    """返回给主程序/API 的稳定业务结果。

    ``@dataclass`` 会自动生成初始化方法等样板代码；``frozen=True`` 表示创建后不能
    修改字段，防止答案文本和引用来源在传递途中被意外改掉。
    """

    text: str
    sources: tuple[str, ...]


class CustomerSupportAssistant:
    """编排 Retriever 与 LLM，并执行客服问答的核心业务规则。

    它是本项目的“业务大脑”：先检查问题、再找证据，证据不足时拒答；只有证据存在
    才请求大模型组织语言，最后从原始文档生成可追踪的来源列表。
    """

    def __init__(self, retriever: Retriever, model: ChatModel):
        # 依赖从外部传入：bootstrap 使用真实对象，测试使用 Fake 对象。
        # 因而本类无需知道模型如何联网、向量库如何创建，职责更单一。
        self.retriever = retriever
        self.model = model

    def ask(self, question: str) -> SupportAnswer:
        """回答一个问题；这是主程序、未来 API 和评测复用的唯一业务入口。"""

        # 1. 把连续空白（空格、换行、Tab）压成一个空格，减少无意义的检索差异。
        normalized = " ".join(question.split())

        # 2. 无效输入在检索和模型调用前失败，避免浪费计算资源。
        if not normalized:
            raise ValueError("问题不能为空")

        # 3. Retriever 返回与问题相关的 Document；每个 Document 包含正文和 metadata。
        # metadata 是“描述数据的数据”，这里用它保存来源文件名和文档块编号。
        documents = self.retriever.invoke(normalized)

        return self.answer_from_documents(normalized, documents)

    def answer_from_documents(
        self, question: str, documents: list[Document]
    ) -> SupportAnswer:
        """根据已经检索到的资料生成回答，不再次执行检索。

        ``ask`` 和 LangGraph 工作流都会复用这个方法：前者自己先检索，后者已经在
        ``retrieve`` 节点取得文档。集中这段逻辑可保证两条路径的拒答、模型异常和来源
        规则完全一致。
        """

        # 阈值过滤后没有 Document 时直接拒答。这里故意不调用 model。
        if not documents:
            return SupportAnswer(REFUSAL, ())

        # 只把本次实际检索到的正文组合成模型上下文。
        # ``\n\n`` 是两个换行，能让不同文档块之间有清晰分隔。
        context = "\n\n".join(document.page_content for document in documents)
        messages = PROMPT.invoke({"context": context, "question": question}).to_messages()

        # 6. 模型负责把证据组织成自然语言，不负责决定引用来源。
        # 模型调用可能失败（如 Ollama 临时不可用返回 502、网络中断等），
        # 这里捕获异常并给出友好提示，而不是直接让整个会话崩溃退出。
        try:
            response = self.model.invoke(messages)
        except Exception as exc:  # noqa: BLE001 - 此处需要兜底所有 provider 的瞬时错误
            return SupportAnswer(
                f"模型暂时无法响应（{type(exc).__name__}），请稍后重试或转人工客服。",
                (),
            )
        # LangChain ChatModel 通常返回带 content 的 AIMessage；兼容测试中的简单对象。
        answer = str(getattr(response, "content", response)).strip() or REFUSAL

        # 引用只从 Document.metadata 生成。dict.fromkeys 在保留顺序的同时去重。
        # Path(...).name 只暴露文件名，不把开发者本机绝对路径返回给用户。
        sources = tuple(
            dict.fromkeys(
                Path(str(document.metadata.get("source", "unknown"))).name
                for document in documents
            )
        )
        return SupportAnswer(answer, sources)
