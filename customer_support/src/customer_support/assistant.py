"""编排检索与模型调用，执行客服问答的稳定业务规则。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate


# 拒答文案集中定义，正式代码和测试共享同一个业务约定。
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
    """只描述 assistant 真正需要的检索能力，而不是绑定 Chroma 具体类型。"""

    def invoke(self, question: str) -> list[Document]: ...


class ChatModel(Protocol):
    """真实聊天模型与测试 FakeModel 都要提供 invoke 方法。"""

    def invoke(self, messages): ...


@dataclass(frozen=True)
class SupportAnswer:
    """返回给 CLI/API 的稳定业务结果，不直接泄露 LangChain 内部对象。"""

    text: str
    sources: tuple[str, ...]


class CustomerSupportAssistant:
    """编排 Retriever 与 LLM，并执行 Day51 的四条核心业务规则。"""

    def __init__(self, retriever: Retriever, model: ChatModel):
        # 依赖从外部传入：bootstrap 使用真实对象，测试使用 Fake 对象。
        self.retriever = retriever
        self.model = model

    def ask(self, question: str) -> SupportAnswer:
        """回答一个问题；这是 CLI、未来 API 和评测都应复用的唯一业务入口。"""
        # 1. 把连续空白（空格、换行、Tab）压成一个空格，减少无意义的检索差异。
        normalized = " ".join(question.split())

        # 2. 无效输入在检索和模型调用前失败，避免浪费计算资源。
        if not normalized:
            raise ValueError("问题不能为空")

        # 3. Retriever 返回与问题相关的 Document；每个 Document 包含正文和 metadata。
        documents = self.retriever.invoke(normalized)

        # 4. 阈值过滤后没有 Document 时直接拒答。这里故意不调用 model。
        if not documents:
            return SupportAnswer(REFUSAL, ())

        # 5. 只把本次实际检索到的正文组合成模型上下文。
        context = "\n\n".join(document.page_content for document in documents)
        messages = PROMPT.invoke({"context": context, "question": normalized}).to_messages()

        # 6. 模型负责把证据组织成自然语言，不负责决定引用来源。
        response = self.model.invoke(messages)
        # LangChain ChatModel 通常返回带 content 的 AIMessage；兼容测试中的简单对象。
        answer = str(getattr(response, "content", response)).strip() or REFUSAL

        # 7. 引用只从 Document.metadata 生成。dict.fromkeys 在保留顺序的同时去重。
        # Path(...).name 只暴露文件名，不把开发者本机绝对路径返回给用户。

        source_names: list[str] = []

        for document in documents:
            source = document.metadata.get("source")

            if not source:
                continue

            filename = Path(str(source)).name

            if filename:
                source_names.append(filename)

        sources = tuple(dict.fromkeys(source_names))

        return SupportAnswer(answer, sources)
